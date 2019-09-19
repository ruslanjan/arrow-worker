import os
import subprocess

from flask import Flask


class Sandbox:
    """
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
    stdin_data: input data
    """

    def __init__(self, app: Flask, container_wall_timelimit,
                 wall_timelimit: int, timelimit: int, memory_limit: int,
                 app_path: str, folder: str,
                 vm_name: str, code: str,
                 run_config: dict, stdin_data: str):
        self.app = app
        self.container_wall_timelimit = container_wall_timelimit
        self.wall_timelimit = wall_timelimit
        self.timelimit = timelimit
        self.memory_limit = memory_limit
        self.app_path = app_path
        # folder were code is contained. look like: self.app_path + self.folder
        self.folder = folder
        self.vm_name = vm_name
        self.code = code
        self.run_config = run_config
        self.stdin_data = stdin_data
        self.app.logger.info('Sandbox created')

    @property
    def run(self) -> dict:
        return self.prepare()

    def prepare(self):
        """
        copying payload, usercode and input to temp directory
        """
        # Copy payload
        cp = subprocess.run(
            f'mkdir {self.app_path}{self.folder} && cp {self.app_path}/Payload/* {self.app_path}{self.folder} && chmod 777 {self.app_path}{self.folder}',
            shell=True)
        if cp.returncode != 0:
            self.app.logger.error(
                f'COMMAND FAILED: mkdir {self.app_path}{self.folder} && cp {self.app_path}/Payload/* {self.app_path}{self.folder} && chmod 777 {self.app_path}{self.folder}')
            return self.internal_error()

        # Writing code and input
        code_file_path = f'{self.app_path}{self.folder}/{self.run_config["file"]}'
        input_file_path = f'{self.app_path}{self.folder}/inputFile'
        try:
            code_file = open(code_file_path, 'w')
            code_file.write(self.code)
            code_file.close()
        except IOError:
            self.app.logger.error(
                f'FAILED TO WRITE/OPEN FILE: {code_file_path}')
            return self.internal_error()
        try:
            input_file = open(input_file_path, 'w')
            input_file.write(self.stdin_data)
            input_file.close()
        except IOError:
            self.app.logger.error(
                f'FAILED TO WRITE/OPEN FILE: {input_file_path}')
            return self.internal_error()

        return self.execute()

    def internal_error(self):
        subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return {
            'output': '',
            'errors': 'Internal error, see logs',
        }

    def execute(self):
        """
        executing usercode with given input.
        steps:
        create docker container with parameters "--cap-add=ALL --privileged --rm -d -m 512M -i -t"
        """

        # env TEMP_DIR is for local run purpose only
        st = f'docker run --cap-add=ALL --privileged --rm -d -m 512M -i -t -v  "{(os.getenv("TEMP_DIR") + "/" if os.getenv("TEMP_DIR") else self.app_path)}{self.folder}":/usercode ' + \
             f'{self.vm_name} /usercode/script.sh "{self.run_config["compilerScript"]}" {str(self.memory_limit)} {str(self.timelimit)} {self.wall_timelimit} {self.run_config["runnerScript"]}'
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
            subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
            return {
                'output': '',
                'errors': 'Wall time exceeded\nInternal error, see logs',
            }
        except subprocess.CalledProcessError:
            pass
        except Exception:
            subprocess.run(f'docker kill {str(container_id)}',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True)
            subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
            return self.internal_error()
        print('container exited successfully')
        meta = str()
        try:
            fs = open(f'{self.app_path}{self.folder}/meta')
            meta = fs.read()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: meta. some how sandbox failed')
            return self.internal_error()
        parsed_meta = dict()
        print(meta)
        for i in meta.split('\n'):
            if i != '':
                parsed_meta[i[0:i.find(':')]] = i[i.find(':') + 1:]
        prepareLogs = ''
        outputFile = ''
        executionErrors = ''
        try:
            fs = open(f'{self.app_path}{self.folder}/prepareLogs')
            prepareLogs = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /prepareLogs')
        try:
            fs = open(f'{self.app_path}{self.folder}/outputFile')
            outputFile = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /outputFile')
        if 'max-rss' in parsed_meta and 'time' in parsed_meta:
            outputFile += f'''\n=====\nИспользовано: {parsed_meta["time"]} с, {parsed_meta["max-rss"]} КБ'''
        try:
            fs = open(f'{self.app_path}{self.folder}/executionErrors')
            errors = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /executionErrors')
        data = {
            'prepareLogs': prepareLogs,
            'outputFile': outputFile,
            'executionErrors': executionErrors,
            'meta': parsed_meta,
        }
        subprocess.run(f'rm -r {self.app_path}{self.folder}', shell=True)
        return data
