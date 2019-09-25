import json
import os
import secrets

from flask import Flask, request, jsonify

from arrow.sandbox import DefaultSandbox
from arrow.run_configs import default_run_configs

app = Flask(__name__)


@app.route('/')
def hello_world():
    return open('templates/index.html').read()


# public run config
@app.route('/run', methods=["POST"])
def run():
    data = json.loads(request.data)
    app_path = os.path.dirname(os.path.realpath(__file__)) + '/'

    container_wall_timelimit = 300
    wall_timelimit = 20

    # these parameters might be used by judge
    timelimit = 2
    memory_limit = 512 * 1000

    files = {
        default_run_configs[data['lang']][0]: data['code'],
        'usercode/input_file': data['stdin'],
        'prepare.sh': default_run_configs[data['lang']][1],
        'post.sh': default_run_configs[data['lang']][3]
    }

    sandbox = DefaultSandbox(app=app,
                             container_wall_timelimit=container_wall_timelimit,
                             wall_timelimit=wall_timelimit,
                             timelimit=timelimit,
                             memory_limit=memory_limit,
                             app_path=app_path,
                             files=files,
                             runner_command=default_run_configs[data['lang']][2])
    return jsonify(sandbox.run)


@app.route('/custom_run', methods=["POST"])
def custom_run():
    data = json.loads(request.data)
    app_path = os.path.dirname(os.path.realpath(__file__)) + '/'

    container_wall_timelimit = 300
    files = {
        default_run_configs[data['lang']][0]: data['code'],
        'usercode/input_file': data['stdin'],
        'prepare.sh': default_run_configs[data['lang']][1],
        'post.sh': default_run_configs[data['lang']][3]
    }

    sandbox = DefaultSandbox(app=app,
                             container_wall_timelimit=container_wall_timelimit,
                             wall_timelimit=data['wall_timelimit'],
                             timelimit=data['time_limit'],
                             memory_limit=data['memory_limit'],
                             app_path=app_path,
                             files=data['files'],
                             runner_command=data['runner_command'])
    return jsonify(sandbox.run)


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
