import json
import os

from flask import Flask, request, jsonify

from arrow.run_configs import default_run_configs
from arrow.sandbox import DefaultSandbox
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route('/')
def index():
    return 'kek'


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
                             run_command=default_run_configs[data['lang']][2])
    return jsonify(sandbox.run)


@app.route('/custom_run', methods=["POST"])
def custom_run():
    data = json.loads(request.data)
    app_path = os.path.dirname(os.path.realpath(__file__)) + '/'

    container_wall_timelimit = 300

    sandbox = DefaultSandbox(app=app,
                             container_wall_timelimit=container_wall_timelimit,
                             wall_timelimit=data['wall_timelimit'],
                             timelimit=data['time_limit'],
                             memory_limit=data['memory_limit'],
                             app_path=app_path,
                             files=data['files'],
                             run_command=data['run_command'])
    return jsonify(sandbox.run)


if __name__ == '__main__':
    app.run(threaded=False)
    # "threaded=False" very important. because if we
    # have parallel
    # request than this will crash isolate
