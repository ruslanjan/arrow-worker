#!/usr/bin/env bash

#This file is for docker

cd /app

#python3 app.py
#flask run --host 0.0.0.0
gunicorn -w 1 -b 0.0.0.0:5000 app:app