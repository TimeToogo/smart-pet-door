#!/bin/bash

set -e

DIR="$(dirname $(dirname $(realpath $0)))"
cd $DIR

if [[ ! -e "$DIR/.virtualenv" ]];
then
    echo "venv does not exist, creating..."
    python3 -m venv $DIR/.virtualenv
    source $DIR/.virtualenv/bin/activate
    pip install -r $DIR/requirements.txt
fi

if [[ -z "$VIRTUAL_ENV" ]];
then
    echo "activating venv..."
    source $DIR/.virtualenv/bin/activate
fi

echo "starting process..."
python -m src.main > execution.log 2>&1 &
exit 0
