#!/bin/bash

DIR="$(dirname $(dirname $(realpath $0)))"

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
python $DIR/src/main.py &
exit 0
