#!/bin/sh

set -e

host="$1"
port="$2"
shift 2
exec_cmd="$@"

until python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('$host', $port))"; do
  >&2 echo "Service $host:$port is unavailable - sleeping"
  sleep 1
done

>&2 echo "Service $host:$port is up - executing command"
exec $exec_cmd