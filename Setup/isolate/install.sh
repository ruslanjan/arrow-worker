#!/bin/sh

cd /isolate
make isolate
make install
#isolate-check-environment