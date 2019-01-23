import json
import os
import secrets
import logging

from flask import Flask, request

from languages import languages
from sandbox import Sandbox

app = Flask(__name__)


@app.route('/')
def hello_world():
    return open('templates/index.html').read()


@app.route('/run', methods=["POST"])
def run():
    data = json.loads(request.data)
    folder = 'temp/' + secrets.token_hex(16)
    vm_name = 'virtual_machine'
    path = os.path.dirname(os.path.realpath(__file__)) + '/'

    container_wall_timelimit = 60
    wall_timelimit = 10

    # these parameters might be used by judge
    timelimit = 2
    memory_limit = 256 * 1000

    sandbox = Sandbox(app, container_wall_timelimit, wall_timelimit, timelimit, memory_limit, path, folder, vm_name, data['code'], languages[data['lang']], data['stdin'])
    return json.dumps(sandbox.run)


def submit():
    data = json.loads(request.data)
    folder = 'temp/' + secrets.token_hex(16)
    vm_name = 'virtual_machine'
    path = os.path.dirname(os.path.realpath(__file__)) + '/'

    container_wall_timelimit = 60
    wall_timelimit = 10

    # these parameters must be provided
    timelimit = 2
    memory_limit = 256 * 1000

    print(data)

if __name__ == '__main__':
    app.run()