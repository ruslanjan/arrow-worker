import os
import subprocess

from flask import Flask


class DefaultSandboxRunConfig:
    def __init__(self, prepare_script, runner_command, description=''):
        """
        :param prepare_script: bash script executed before runner command
        :param runner_command: command to run executable in sandbox
        :param file: all files that will be added to /usercode/.
        is an array looks like this "{"main.cpp": "#include", "inputFile": '1 2 2 3'}"
        files should be without '/' and files in folders should be ''
        :param description: description of config
        """
        self.prepare_script = prepare_script
        self.runner_command = runner_command
        self.description = description


class DefaultSandbox:
    """
    runner_command stdin file is "input_file", stdout "output_file" and
    stderr "execution_errors".

    app: flask app
    container_wall_timelimit: time limit for container
    wall_timelimit: real time timelimit for code
    timelimit: cpu timelimit for code
    memory_limit: memory_limit for code
    app_path: app_path to app main directory. where payload contains
    folder: folder where code contains. looks like temp/123fgh1234/
    vm_name: sandbox vm name
    code: user code
    run_config: configuration to run
    in_container: if true uses docker container. NOT YET IMPLEMENTED
    container_memory_limit: container memory limit in mega bytes
    """

    def __init__(self, app: Flask, container_wall_timelimit,
                 wall_timelimit: int, timelimit: int, memory_limit: int,
                 app_path: str, folder: str,
                 vm_name: str, files: dict,
                 run_config: DefaultSandboxRunConfig,
                 container_memory_limit=2048, in_container=True):
        self.app = app
        self.container_wall_timelimit = container_wall_timelimit
        self.wall_timelimit = wall_timelimit
        self.timelimit = timelimit
        self.memory_limit = memory_limit
        self.app_path = app_path
        # folder were code is contained. look like: self.app_path + self.folder
        self.folder = folder
        self.vm_name = vm_name
        self.files = files
        self.run_config = run_config
        self.app.logger.info('Sandbox created')
        self.in_container = in_container
        self.container_memory_limit = container_memory_limit

    @property
    def run(self) -> dict:
        res = self.prepare()
        # rm folder to be sure.
        subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return res

    def create_and_write_to_file(self, path, data):
        try:
            path = open(path, 'w')
            path.write(data)
            path.close()
        except IOError:
            self.app.logger.error(
                f'FAILED TO WRITE/OPEN FILE: {path}')
            return self.internal_error()

    def prepare(self):
        """
        copying payload, usercode and input to temp directory
        """
        # Copy payload folder at /app/Payload
        cp = subprocess.run(
            f'mkdir {self.app_path}{self.folder} && cp {self.app_path}/Payload/* {self.app_path}{self.folder} && chmod 777 {self.app_path}{self.folder}',
            shell=True)
        if cp.returncode != 0:
            self.app.logger.error(
                f'COMMAND FAILED: mkdir {self.app_path}{self.folder} && cp {self.app_path}/Payload/* {self.app_path}{self.folder} && chmod 777 {self.app_path}{self.folder}')
            return self.internal_error()

        # Writing code and input
        # code_file_path = f'{self.app_path}{self.folder}/{self.run_config.file}'
        # self.create_and_write_to_file(code_file_path, self.code)
        # input_file_path = f'{self.app_path}{self.folder}/input_file'
        # self.create_and_write_to_file(input_file_path, self.stdin_data)

        # create all request files
        for path, data in self.files.items():
            self.create_and_write_to_file(
                f'{self.app_path}{self.folder}/{path}', data)
        if 'input_file' not in self.files:
            self.create_and_write_to_file(
                f'{self.app_path}{self.folder}/input_file', 'data')

        return self.execute()

    def internal_error(self, message):
        subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return {
            'IE': True,
            'errors': message,
        }

    def run_container(self, run_command):
        """
        runs container and exec run_command inside.
        :param run_command:
        :return:
        """
        st = f'docker run --cap-add=ALL --privileged --rm -d -m {self.container_memory_limit}M -i -t -v  "{(os.getenv("TEMP_DIR") + "/" if os.getenv("TEMP_DIR") else self.app_path)}{self.folder}":/usercode ' + \
             f'{self.vm_name} /usercode/' + run_command
        self.app.logger.info('Docker start command: ' + st)
        container_id = subprocess.run(st, shell=True,
                                      stdout=subprocess.PIPE).stdout.decode(
            "utf-8").rstrip('\n\r')
        try:
            subprocess.run(
                f'docker wait {str(container_id)}',
                timeout=self.container_wall_timelimit,
                stderr=subprocess.PIPE,
                shell=True,
                stdout=subprocess.PIPE)
            subprocess.run(f'docker kill {str(container_id)}',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True)
            subprocess.run(f'docker rm {str(container_id)}',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True)
        except subprocess.TimeoutExpired:
            return self.internal_error('Wall time exceeded\nInternal error, see logs')
        except subprocess.CalledProcessError:
            pass
        except Exception:
            subprocess.run(f'docker kill {str(container_id)}',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True)
            subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
            return self.internal_error('Internal error, see logs')
        self.app.logger.info('container exited successfully')

    def execute(self):
        """
        executing usercode with given input.
        steps:
        1. create docker container with parameters "--cap-add=ALL --privileged --rm -d -m {container_memory_limit}M -i -t"
        1.2. add volume to docker container with usercode to /usercode/ ""{self.app_path}{self.folder}":/usercode"
        2. run docker with script defaultSandboxRunScript and configuration to run using "isolate".
        4. parse isolate meta
        5. parse output

        if return contains "IE" key then docker broke not a usercode fault
        check meta for MLE, TLE, RE, etc...
        :return result of run as dict:
                {
                'prepare_logs': log of prepare_script from stdout
                'prepare_errors': log of prepare_script from stderr
                'output_file':  output of runner_command from stdout
                'execution_errors':  output of runner_command from stderr
                'meta': log of isolate if prepare_script returned 0
                'IE': if true none of above are valid. caught internal error
                }
        """

        run_command = f'defaultSandboxRunScript.sh "{self.run_config.prepare_script}" {str(self.memory_limit)} {str(self.timelimit)} {self.wall_timelimit} {self.run_config.runner_command} '
        if self.in_container or True:
            self.run_container(run_command)
        else:
            pass  # not yet implemented
        meta = str()
        try:
            fs = open(f'{self.app_path}{self.folder}/meta')
            meta = fs.read()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: meta. some how sandbox failed')
            return self.internal_error()
        parsed_meta = dict()
        self.app.logger.info(meta)
        for i in meta.split('\n'):
            if i != '':
                parsed_meta[i[0:i.find(':')]] = i[i.find(':') + 1:]
        prepare_logs = ''
        output_file = ''
        execution_errors = ''
        try:
            fs = open(f'{self.app_path}{self.folder}/prepare_logs')
            prepare_logs = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /prepare_logs')
        try:
            fs = open(f'{self.app_path}{self.folder}/output_file')
            output_file = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /output_file')
        # if 'max-rss' in parsed_meta and 'time' in parsed_meta:
        #     output_file += f'''\n=====\nИспользовано: {parsed_meta["time"]} с, {parsed_meta["max-rss"]} КБ'''
        try:
            fs = open(f'{self.app_path}{self.folder}/execution_errors')
            errors = fs.read()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: /execution_errors')
        data = {
            'prepare_logs': prepare_logs,
            'output_file': output_file,
            'execution_errors': execution_errors,
            'meta': parsed_meta,
            'IE': False
        }
        subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return data
