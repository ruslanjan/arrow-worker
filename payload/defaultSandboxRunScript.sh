#!/bin/bash

path=$1 # path to usecode
prepare=$2
memory=$3
time=$4
wallTime=$5
#input_file=$5

shift 5

runCommand=${@}

cd $path || exit

exec 1>$path/prepare_logs
exec 2>$path/prepare_errors


isolate-check-environment -e
isolate --cg --dir=$path/ --init

touch "$path/meta"
#touch "$path/outputFile"
#chmod 777 "$path/outputFile"
#ls -la > $path/completed

echo "$prepare" > $path/prepare.sh
bash $path/prepare.sh 1>$path/prepare_logs 2>$path/prepare_errors

#if [[ $? == 0 ]]
if [ -s $path/prepare_errors ] # check if we have errors in prepare script or isolate
then
    echo "\nPREPARE_ERROR"
else
    exec  1> $"$path/logs"
    exec  2> $"$path/logs"
    # shellcheck disable=SC2086
    isolate --env=HOME=/root --time=${time} --wall-time=${wallTime} --dir=$path/usercode:rw --stdin=$path/usercode/input_file --stdout=$path/usercode/output_file --stderr=$path/usercode/execution_errors --mem=${memory} --cg -s --meta=$path/meta --chdir=$path/usercode  --run -- ${runCommand}
fi

isolate --cleanup

#exec 1>&3 2>&4

#head -100 $path/logfile.txt
#touch $path/completed

