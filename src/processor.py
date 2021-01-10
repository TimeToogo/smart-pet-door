from config import config

def video_processor(queue, shared):
    while True:
        video = queue.get(block=True)
        config.logger.info('received video %s for processing' % video)

        # TODO