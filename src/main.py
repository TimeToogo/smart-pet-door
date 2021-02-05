from multiprocessing import Process, Queue, Value, Manager
from time import sleep
import signal
import sys
import os
import subprocess

from .config import config, State

from .recorder import start_recorder
from .processor import video_processor
from .temp_monitor import temp_monitor
from .fan_controller import fan_controller
from .auto_updater import auto_updater
from .api import api

def start():
    config.logger.info('starting smart pet door app...')

    manager = Manager()
    state = Value('i', State.ALIVE)
    shared = manager.dict()
    video_queue = Queue()

    procs = []

    procs.append(keep_alive('motion detection recorder', state, start_recorder, (video_queue, shared)))
    procs.append(keep_alive('video processor', state, video_processor, (video_queue, shared)))
    procs.append(keep_alive('temp monitor', state, temp_monitor, (shared,)))
    procs.append(keep_alive('fan controller', state, fan_controller, (shared,)))
    procs.append(keep_alive('auto update', state, auto_updater, (state,)))
    procs.append(keep_alive('api', state, api, ()))

    def wait_for_procs(timeout = 3.0):
        nonlocal procs

        sleep(timeout)

        exit_code = 0
        for p in procs:
            if p.is_alive():
                config.logger.info('proc %d failed to terminate in time' % p.pid)
                p.kill()
                exit_code = 1

        return exit_code

    def sigint_handler(sig, frame):
        nonlocal state

        if state.value == State.TERMINATING:
            return
        
        config.logger.info('handling sigint, shutting down...')

        with state.get_lock():
            state.value = State.TERMINATING

        exit_code = wait_for_procs()
        sys.exit(exit_code)

    signal.signal(signal.SIGINT, sigint_handler)

    while state.value == State.ALIVE:
        sleep(1.0)

    if state.value == State.TERMINATING:
        config.logger.info('finishing process...')
    elif state.value == State.UPDATING or 1:
        config.logger.info('found update, restarting process...')
        wait_for_procs()
        subprocess.Popen(['bash', './scripts/boot.sh'])
        config.logger.info('terminating...')
        sys.exit(0)

def keep_alive(name, state, function, args):
    proc = Process(target=manage_proc, args=(name, state, function, args))
    proc.start()
    return proc

def manage_proc(name, state, function, args):
    while state.value == State.ALIVE:
        try:
            config.logger.info('[%s] starting process' % name) 
            proc = Process(target=function, args=args)
            proc.start()

            while state.value == State.ALIVE and proc.is_alive():
                sleep(1.0)

            if not proc.is_alive():
                config.logger.info('[%s] process finished with code %d' % (name, proc.exitcode))
        except Exception as e:
            config.logger.warning('[%s] process threw exception' % name, exc_info=e)

    if proc.is_alive():
        proc.terminate()
        proc.join(1.0)

    config.logger.info('[%s] process has been terminated' % name)


if __name__ == '__main__':
    start()