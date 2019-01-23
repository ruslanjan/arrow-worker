#!/bin/bash

compiler=$1
memory=$2
time=$3
walltime=$4

shift 4

runner=${@}

isolate-check-environment -e
isolate --cg --dir=/usercode/ --init

echo "" > /usercode/meta

exec  1> $"/usercode/logfile"
exec  2> $"/usercode/errors"

${compiler}

if [[ $? == 0 ]]
then
    isolate --env=HOME=/root --dir=/usr/ --dir=/usercode/  --stdin=/usercode/inputFile  --cg -s --meta=/usercode/meta --chdir=/usercode  --run -- ${runner}
else
    echo "COMPILATION_ERROR"
fi

isolate --cleanup

#exec 1>&3 2>&4

#head -100 /usercode/logfile.txt
#touch /usercode/completed

mv /usercode/logfile /usercode/completed

