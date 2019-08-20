#!/bin/bash
# Currently unused.

set -e

to=$1

shift 1

cont=$(sudo docker run --rm -d "${@}")
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    code=$(gtimeout "$to" docker wait "$cont" || true)
else
    code=$(timeout "$to" docker wait "$cont" || true)
fi
docker kill $cont &> /dev/null
echo -n 'status: '
if [[ -z "$code" ]]; then
    echo wall-timeout
else
    echo exited: $code
fi

echo output:
# pipe to sed simply for pretty nice indentation
docker logs $cont | sed 's/^/\t/'

docker rm $cont &> /dev/null
