#!/bin/bash

prepare=$1
memory=$2
time=$3
wallTime=$4
input_file=$5

shift 5

runCommand=${@}

isolate-check-environment -e
isolate --cg --dir=/usercode/ --init

touch "/usercode/meta"
#touch "/usercode/outputFile"
#chmod 777 "/usercode/outputFile"
#ls -la > /usercode/completed

cd /usercode || exit
echo "$prepare" > ./prepare.sh
bash /usercode/prepare.sh >>/usercode/prepare_logs 2>&1

if [[ $? == 0 ]]
then
    exec  1> $"/usercode/output_file"
    exec  2> $"/usercode/execution_Errors"
    # shellcheck disable=SC2086
    isolate --env=HOME=/root --time=${time} --wall-time=${wallTime} --dir=/usr/ --dir=/usercode/  --stdin=/usercode/${input_file} --mem=${memory} --cg -s --meta=/usercode/meta --chdir=/usercode  --run -- ${runCommand}
else
    echo "COMPILATION_ERROR"
fi

isolate --cleanup

#exec 1>&3 2>&4

#head -100 /usercode/logfile.txt
#touch /usercode/completed

