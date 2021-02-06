#!/usr/bin/env bash
OWN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


sigint_handler()
{
  kill $PID
  exit
}

trap sigint_handler SIGINT

while true; do
  $@ &
  PID=$!
  inotifywait -e modify -e move -e create -e delete -e attrib -r ${OWN_DIR}
  kill $PID
done
