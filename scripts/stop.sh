#!/bin/bash

set -e

if [[ -f main.pid ]];
then
    OLD_PID="$(cat main.pid)"
    if kill -0 $OLD_PID >/dev/null 2>&1;
    then
        echo "stopping existing process $OLD_PID"
        kill -SIGINT $OLD_PID
        while kill -0 $OLD_PID 2> /dev/null; 
        do 
            sleep 1; 
        done;
        echo "processed stopped"
    fi

    rm main.pid
else
    echo "no existing process"
fi

exit 0
