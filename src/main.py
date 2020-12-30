from multiprocessing import Process, Queue, Value
from time import sleep
import signal
import sys
import os

from config import config, State

from recorder import start_recorder
from processor import video_processor
from auto_updater import auto_updater

def start():
    config.logger.info('starting smart pet door app...')

    state = Value('i', State.ALIVE)
    video_queue = Queue()

    procs = []

    procs.append(keep_alive('motion detection recorder', state, start_recorder, (video_queue,)))
    procs.append(keep_alive('video processor', state, video_processor, (video_queue,)))
    procs.append(keep_alive('auto update', state, auto_updater, (state,)))

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
        config.logger.info('handling sigint, shutting down...')
        nonlocal state

        with state.get_lock():
            state.value = State.TERMINATING

        exit_code = wait_for_procs()
        sys.exit(exit_code)

    signal.signal(signal.SIGINT, sigint_handler)

    while state.value == State.ALIVE:
        sleep(1.0)

    if state.value == State.TERMINATING:
        config.logger.info('finishing process...')
    elif state.value == State.UPDATING:
        config.logger.info('found update, restarting process...')
        wait_for_procs()
        os.execl(sys.executable, sys.executable, *sys.argv)

def keep_alive(name, state, function, args):
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
                config.logger.warning('[%s] process threw exception', exc_info=e)

        if proc.is_alive():
            proc.terminate()
            proc.join(1.0)

        config.logger.info('[%s] process has been terminated' % name)

    proc = Process(target=manage_proc, args=(name, state, function, args))
    proc.start()
    return proc


if __name__ == '__main__':
    start()