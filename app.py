import json
import os
import secrets

from flask import Flask, request

from defaultsandbox import DefaultSandbox, DefaultSandboxRunConfig
from run_configs import default_run_configs

app = Flask(__name__)


@app.route('/')
def hello_world():
    return open('templates/index.html').read()


# public run config
@app.route('/run', methods=["POST"])
def run():
    data = json.loads(request.data)
    folder = 'temp/' + secrets.token_hex(16)
    vm_name = 'virtual_machine'
    path = os.path.dirname(os.path.realpath(__file__)) + '/'

    container_wall_timelimit = 300
    wall_timelimit = 20

    # these parameters might be used by judge
    timelimit = 2
    memory_limit = 512 * 1000

    files = {
        default_run_configs[data['lang']][0]: data['code'],
        'input_file': data['stdin']
    }

    sandbox = DefaultSandbox(app,
                             container_wall_timelimit,
                             wall_timelimit,
                             timelimit,
                             memory_limit,
                             path,
                             folder,
                             vm_name,
                             files,
                             default_run_configs[data['lang']][1],
                             'input_file')
    return json.dumps(sandbox.run)


@app.route('/custom_run', methods=["POST"])
def custom_run():
    data = json.loads(request.data)
    folder = 'temp/' + secrets.token_hex(16)
    vm_name = 'virtual_machine'
    path = os.path.dirname(os.path.realpath(__file__)) + '/'
    container_wall_timelimit = 300
    wall_timelimit = 20

    config = DefaultSandboxRunConfig(**data['files'])

    sandbox = DefaultSandbox(app,
                             container_wall_timelimit,
                             wall_timelimit,
                             data['timelimit'],
                             data['memory_limit'],
                             path,
                             folder,
                             vm_name,
                             data['files'],
                             config,
                             'input_file')

    return json.dumps(sandbox.run)


# def submit():
#     data = json.loads(request.data)
#     folder = 'temp/' + secrets.token_hex(16)
#     vm_name = 'virtual_machine'
#     path = os.path.dirname(os.path.realpath(__file__)) + '/'
#
#     container_wall_timelimit = 60
#     wall_timelimit = 10
#
#     # these parameters must be provided
#     timelimit = 2
#     memory_limit = 256 * 1000
#
#     print(data)


if __name__ == '__main__':
    app.run()
