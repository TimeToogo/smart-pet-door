from time import sleep
import subprocess
import os
import sys

from .config import config, State

def auto_updater(state):
   while True:
        updated = perform_update()

        if updated:
            with state.get_lock():
                state.value = State.UPDATING
            return

        sleep(float(config.AD_INTERVAL_S)) 

def run(cmd: str, out_enc = 'utf8') -> bytes:
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return proc.stdout.read().decode(out_enc)

def perform_update():
    config.logger.info('checking if update...')
    current_rev = run('git rev-parse HEAD')
    config.logger.info('current revision at %s' % current_rev)

    os.system('git pull')

    new_rev = run('git rev-parse HEAD')
    config.logger.info('new revision at %s' % new_rev)

    return current_rev != new_rev