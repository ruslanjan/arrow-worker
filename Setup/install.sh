#!/bin/sh

cd /app/Setup

docker build -t 'virtual_machine' - < Dockerfile

cd /app

pip install -r requirements.txt
