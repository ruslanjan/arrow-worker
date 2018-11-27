#!/bin/sh

cd /app/Setup

docker build -t 'virtual_machine' - < Dockerfile

cd /app/API

npm install
