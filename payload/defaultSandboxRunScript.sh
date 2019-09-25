#!/bin/bash

path=$1 # path to sandbox
memory=$2 # isolate memory limit
time=$3 # isolate time limit
wallTime=$4

shift 4

runCommand=${@}

cd $path || exit

touch "$path/meta"
touch "$path/patload_files"

isolate-check-environment -e
isolate --cg --init

exec  1> $"$path/logs"
exec  2> $"$path/logs"

/bin/su -c "/bin/bash prepare.sh" dummy #1>$path/prepare_logs 2>$path/prepare_errors

#if [[ $? == 0 ]]
if [ -s $path/prepare_errors ] # check if we have errors in prepare script or isolate
then
    : #    printf "\nPREPARE_ERROR" > $path/logs
else
    # shellcheck disable=SC2086
    isolate -s --env=HOME=/root --time=${time} --wall-time=${wallTime} --dir=$path/usercode:rw --stdin=$path/usercode/input_file --stdout=$path/usercode/output_file --stderr=$path/usercode/error_file --mem=${memory} --cg --meta=$path/meta --chdir=$path/usercode  --run -- ${runCommand}
fi

#exec 1> $path/post_logs
#exec 2> $path/post_errors

# leave additional file paths and their name in payload_files to get them in request. AHTUNG usecode output is not returned by default
/bin/su -c "/bin/bash post.sh" dummy #1>$path/post_logs 2>$path/post_errors


isolate --cleanup --cg
