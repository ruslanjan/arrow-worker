import os
import subprocess

from flask import Flask


class DefaultRunConfig:
    def __init__(self, prepare_script, runner_command, description=''):
        """
        :param prepare_script: bash script executed before runner command
        :param runner_command: command to run executable in sandbox.
        runner command looks like '{0}/a.out' where "{0}" stands for path to woking dir.
        :param file: all files that will be added to some path. path you will get path as param
        is an dict that looks like this "{"main.cpp": "#include", "inputFile": '1 2 2 3'}"
        files should not start with '/'. currently folders are supperted as 'kek/asd.cpp'
        :param description: description of config
        """
        self.prepare_script = prepare_script
        self.runner_command = runner_command
        self.description = description

    def format_runner_command(self, path):
        return self.runner_command.format(path)


class DefaultSandbox:
    """
    DOCKER SUPPORT REMOVED
    container time limit is now a prepare and post script + usercode timelimit

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
                 run_config: DefaultRunConfig,
                 container_memory_limit=2048):
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
        self.container_memory_limit = container_memory_limit

    @property
    def run(self) -> dict:
        res = self.prepare()
        # rm folder to be sure.
        # subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return res

    def create_and_write_to_file(self, path, data):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
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
        
        # Copy payload folder at /app/payload
        cp = subprocess.run(
            f'mkdir {self.app_path}{self.folder} && cp -rp {self.app_path}/payload/* {self.app_path}{self.folder}',
            shell=True)
        if cp.returncode != 0:
            self.app.logger.error(
                f'COMMAND FAILED:Copy payload failed ')
            return self.internal_error('Copy payload failed')

        # Writing code and input
        # code_file_path = f'{self.app_path}{self.folder}/{self.run_config.file}'
        # self.create_and_write_to_file(code_file_path, self.code)
        # input_file_path = f'{self.app_path}{self.folder}/input_file'
        # self.create_and_write_to_file(input_file_path, self.stdin_data)

        # create all request files
        for path, data in self.files.items():
            self.create_and_write_to_file(
                f'{self.app_path}{self.folder}/{path}', data)

        # cp = subprocess.run(f'chmod -R 777 {self.app_path}{self.folder}', shell=True)
        return self.execute()

    def internal_error(self, message):
        subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return {
            'IE': True,
            'errors': message,
        }


    def execute(self):
        """
        executing usercode with given input.
        steps:
        2. run script defaultSandboxRunScript and configuration to run using "isolate".
        4. parse isolate meta
        5. parse output

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

        run_command = f'defaultSandboxRunScript.sh {self.app_path}{self.folder} "{self.run_config.prepare_script}" {str(self.memory_limit)} {str(self.timelimit)} {self.wall_timelimit} {self.run_config.format_runner_command(self.app_path + self.folder + "/usercode")} '
        try:
            subprocess.run(f'{self.app_path}{self.folder}/{run_command}',   
                            timeout=self.container_wall_timelimit,
                                stderr=subprocess.PIPE,               
                                    shell=True,                           
                                        stdout=subprocess.PIPE)
        except subprocess.TimeoutExpired:                                               
                return self.internal_error('Wall time exceeded\nInternal error, see logs')  
        except subprocess.CalledProcessError:
                pass                             
        except:
            subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
            return self.internal_error('Internal error, see logs')
        meta = str()
        try:
            fs = open(f'{self.app_path}{self.folder}/meta')
            meta = fs.read()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: meta. some how sandbox failed')
            return self.internal_error('FAILED TO WRITE/OPEN FILE: meta. some how sandbox failed')
        parsed_meta = dict()
        self.app.logger.info(meta)
        for i in meta.split('\n'):
            if i != '':
                parsed_meta[i[0:i.find(':')]] = i[i.find(':') + 1:]
        prepare_logs = ''
        logs = ''
        output_file = ''
        execution_errors = ''
        try:
            fs = open(f'{self.app_path}{self.folder}/prepare_logs')
            prepare_logs = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /prepare_logs')
        try:
            fs = open(f'{self.app_path}{self.folder}/usercode/output_file')
            output_file = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /usercode/output_file')
        # if 'max-rss' in parsed_meta and 'time' in parsed_meta:
        #     output_file += f'''\n=====\nИспользовано: {parsed_meta["time"]} с, {parsed_meta["max-rss"]} КБ'''
        try:
            fs = open(f'{self.app_path}{self.folder}/usercode/execution_errors')
            execution_errors = fs.read()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: /usercode/execution_errors')
        data = {
            'prepare_logs': prepare_logs,
            'output_file': output_file,
            'logs': logs,
            'execution_errors': execution_errors,
            'meta': parsed_meta,
            'IE': False
        }
        # subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return data
