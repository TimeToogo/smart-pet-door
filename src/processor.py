import tflite_runtime.interpreter as tflite
import numpy as np
from multiprocessing import Queue
import subprocess
import os
import uuid
import shutil
from datetime import datetime

from .config import config
from .ml.preprocess import preprocess_video
from .ml.class_map import class_map
from . import db

def video_processor(queue, shared):
    model = load_tflite_model()
    dbcon = db.connect()

    os.makedirs(config.VP_FRAMES_DIR, exist_ok=True)
    os.makedirs(config.VP_PUBLIC_DIR, exist_ok=True)

    while True:
        video = queue.get(block=True)
        config.logger.info('received video %s for processing' % video)

        if video['path'].endswith('.avi'):
            config.logger.info('converting avi to mp4')
            video['path'] = convert_video_to_mp4(video['path'])

        if video['type'] != 'motion':
            config.logger.info('video type is %s, not processing' % video['type'])
            continue

        pet, event = classify_video(video['path'], model)

        if not pet or not event:
            config.logger.info('video classified as DISCARD, ignoring...')
            continue

        video_file_name = link_to_pub_dir(video)
        frame_file_path = generate_video_frame(video)
        frame_file_name = link_to_pub_dir(frame_file_path)

        db.insert_event(dbcon, {
            'timestamp': datetime.now(),
            'pets': [pet],
            'event': event,
            'video_file_name': video_file_name,
            'frame_file_name': frame_file_name
        })

        config.logger.info('finished processing %s' % video)

def convert_video_to_mp4(video_path):
    mp4_path = video_path.replace('.avi', '.mp4')
    os.system('ffmpeg -hide_banner -loglevel error -y -threads %d -i %s -vcodec libx264 -movflags +faststart %s' 
        % (config.VP_FFMPEG_THREADS, video_path, mp4_path))
    config.logger.info('finished converting video to mp4 at %s' % mp4_path)
    os.remove(video_path)

    return mp4_path

def load_tflite_model():
    config.logger.info('loading tflite model from %s' % config.VP_TFLITE_MODEL_PATH)
    interpreter = tflite.Interpreter(model_path=config.VP_TFLITE_MODEL_PATH)
    interpreter.allocate_tensors()
    config.logger.info('loaded model')

    return interpreter

def classify_video(video_path: str, model):
    config.logger.info('preprocessing video %s' % video_path)
    model_input = preprocess_video(video_path)
    config.logger.info('preprocessed video')
    
    config.logger.info('classifying %s' % video_path)

    input_details = model.get_input_details()
    tensor_index = model.get_input_details()[0]['index']

    batched_shape = (1,) + config.VC_INPUT_SHAPE
    model_input = model_input.reshape(batched_shape)
    model.set_tensor(input_details[0]['index'], model_input)

    model.invoke()

    output_details = model.get_output_details()
    prediction = model.get_tensor(output_details[0]['index'])

    class_prediction = np.argmax(prediction[0])

    if class_map[class_prediction] == 'DISCARD':
        return (None, None)

    pet_class, event_class = class_map[class_prediction]
    
    pet_str = ", ".join([pet_str for pet_str, _class in config.VC_PET_CLASSES.items() if _class == pet_class])
    event_str = ", ".join([event_str for event_str, _class in config.VC_EVENT_CLASSES.items() if _class == pet_class])

    config.logger.info('detected pets [%s] in event [%s]' % (pet_str, event_str))

    return pet_class, event_class

def generate_video_frame(video_path):
    file_name = os.path.basename(video_path)[:-4]
    out_path = config.VP_FRAMES_DIR + '/frame-' + file_name + '.jpg'
    
    config.logger.info('saving video frame to %s' % out_path)

    subprocess.run([
        'ffmpeg',
        '-v',
        'error',
        '-i',
        video_path,
        '-vf', 
        'select=eq(n\,10)',
        '-vframes', 
        '1', 
        '-y',
        out_path
    ])

    return out_path

def link_to_pub_dir(path):
    ext = path.split('.')[-1]

    link_name = str(uuid.uuid4()) + '.' + ext
    link_path = config.VP_PUBLIC_DIR + '/' + link_name
    path = os.path.realpath(path)

    config.logger.info('linking %s to %s' % (link_path, path))
    os.link(path, link_path)

    return link_name

if __name__ == '__main__':
    queue = Queue()
    queue.put({'type': 'motion', 'path': '/Users/elliotlevin/Temp/motion/dataset/motion.2021-02-04T18-32-03.mp4'})
    video_processor(queue, {})