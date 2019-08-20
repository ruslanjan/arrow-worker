import os
import subprocess

from flask import Flask


class Sandbox:
    def __init__(self, app: Flask, container_wall_timelimit,
                 wall_timelimit: int, timelimit: int, memory_limit: int,
                 path: str, folder: str,
                 vm_name: str, code: str,
                 lang: dict, stdin_data: str):
        self.app = app
        self.container_wall_timelimit = container_wall_timelimit
        self.wall_timelimit = wall_timelimit
        self.timelimit = timelimit
        self.memory_limit = memory_limit
        self.path = path
        # folder were code is contained. look like: self.path + self.folder
        self.folder = folder
        self.vm_name = vm_name
        self.code = code
        self.lang = lang
        self.stdin_data = stdin_data
        self.app.logger.info('Sandbox created')

    @property
    def run(self) -> dict:
        return self.prepare()

    def prepare(self):
        # Copy payload
        cp = subprocess.run(
            'mkdir ' + self.path + self.folder + ' && cp ' + self.path +
            '/Payload/* ' + self.path + self.folder + '&& chmod 777 ' + self.path +
            self.folder, shell=True)
        if cp.returncode != 0:
            self.app.logger.error(
                'COMMAND FAILED: ' + 'mkdir ' + self.path + self.folder + ' && cp ' + self.path +
                '/Payload/* ' + self.path + self.folder + '&& chmod 777 ' + self.path +
                self.folder)
            return self.internal_error()

        # Writing code and input
        code_file_path = self.path + self.folder + '/' + self.lang['file']
        input_file_path = self.path + self.folder + '/inputFile'
        try:
            code_file = open(code_file_path, 'w')
            code_file.write(self.code)
            code_file.close()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: ' + code_file_path)
            return self.internal_error()
        try:
            input_file = open(input_file_path, 'w')
            input_file.write(self.stdin_data)
            input_file.close()
        except IOError:
            self.app.logger.error(
                'FAILED TO WRITE/OPEN FILE: ' + input_file_path)
            return self.internal_error()

        return self.execute()

    def internal_error(self):
        subprocess.run('rm -r ' + self.path + self.folder, shell=True)
        return {
            'output': '',
            'errors': 'Internal error, see logs',
        }

    def execute(self):
        st = 'docker run --cap-add=ALL --privileged --rm -d' + ' -m 512M -i -t -v  "' + (
            os.getenv('TEMP_DIR') + '/' if os.getenv('TEMP_DIR')
            else self.path) + self.folder + '":/usercode ' + \
             self.vm_name + ' /usercode/script.sh ' + self.lang[
                 'compilerScript'] + ' ' \
             + str(self.memory_limit) + ' ' + str(self.timelimit) + ' ' + str(
            self.wall_timelimit) + ' ' + \
             self.lang['runnerScript']
        self.app.logger.info('Docker start command: ' + st)
        container_id = subprocess.run(st, shell=True,
                                      stdout=subprocess.PIPE).stdout.decode(
            "utf-8").rstrip('\n\r')
        try:
            subprocess.run('docker wait ' + str(container_id),
                           timeout=self.container_wall_timelimit,
                           stderr=subprocess.PIPE,
                           shell=True,
                           stdout=subprocess.PIPE)
            subprocess.run('docker kill ' + str(container_id),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True)
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'errors': 'Wall time exceeded\nInternal error, see logs',
            }
        except subprocess.CalledProcessError:
            pass
        except Exception:
            subprocess.run('docker kill ' + str(container_id),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True)
            return self.internal_error()
        meta = str()
        try:
            fs = open(self.path + self.folder + '/meta')
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
        output = ''
        errors = ''
        try:
            fs = open(self.path + self.folder + '/completed')
            output = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /completed')
        if 'max-rss' in parsed_meta and 'time' in parsed_meta:
            output += '\n=====\nИспользовано: ' + parsed_meta['time'] + ' с, ' + \
                      parsed_meta['max-rss'] + ' КБ'
        try:
            fs = open(self.path + self.folder + '/errors')
            errors = fs.read()
        except IOError:
            self.app.logger.error('FAILED TO WRITE/OPEN FILE: /errors')
        data = {
            'output': output,
            'errors': errors,
            'meta': parsed_meta,
        }
        subprocess.run('rm -r ' + self.path + self.folder, shell=True)
        return data
