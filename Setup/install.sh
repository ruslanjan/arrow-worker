#!/bin/sh

cd /app
pip3 install -r requirements.txt
mkdir --mod=222 temp
chmod 222 temp
chmod -R 666 /app/payload/usercode
chmod 667 /app/payload/usercode
