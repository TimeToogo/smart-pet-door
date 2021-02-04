import tflite_runtime.interpreter as tflite
import numpy as np
from multiprocessing import Queue
import subprocess
import os
import uuid
import shutil
from datetime import datetime

from config import config
from ml.preprocess import preprocess_video
import db

def video_processor(queue, shared):
    model = load_tflite_model()
    dbcon = db.connect()

    os.makedirs(config.VP_FRAMES_DIR, exist_ok=True)
    os.makedirs(config.VP_PUBLIC_DIR, exist_ok=True)

    while True:
        video = queue.get(block=True)
        config.logger.info('received video %s for processing' % video)

        pets, event = classify_video(video, model)

        if event == config.VC_EVENT_CLASSES['DISCARD']:
            config.logger.info('video classified as DISCARD, ignoring...')
            continue

        if len(pets) == 0:
            config.logger.info('did not detect pets in video, ignoring...')
            continue

        video_file_name = link_to_pub_dir(video)
        frame_file_path = generate_video_frame(video)
        frame_file_name = link_to_pub_dir(frame_file_path)

        db.insert_event(dbcon, {
            'timestamp': datetime.now(),
            'pets': pets,
            'event': event,
            'video_file_name': video_file_name,
            'frame_file_name': frame_file_name
        })

        config.logger.info('finished processing %s' % video)

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
    model.set_tensor(input_details[0]['index'], model_input.reshape(batched_shape))

    model.invoke()

    output_details = model.get_output_details()
    pet_index = next(x['index'] for x in output_details if x['shape'][1] == len(config.VC_PET_CLASSES))
    event_index = next(x['index'] for x in output_details if x['shape'][1] == len(config.VC_EVENT_CLASSES))
    pet_results = model.get_tensor(pet_index)
    event_results = model.get_tensor(event_index)

    pet_class_indexes = [k for k, x in enumerate(pet_results[0].tolist()) if x > config.VP_PET_CLASS_THRESHOLD]
    event_class_index = np.argmax(event_results[0]).tolist()

    all_pet_classes = list(config.VC_PET_CLASSES.items())
    all_event_classes = list(config.VC_EVENT_CLASSES.items())
    
    pet_str = ", ".join([all_pet_classes[x][0] for x in pet_class_indexes])
    event_str = all_event_classes[event_class_index][0]

    config.logger.info('detected pets [%s] in event [%s]' % (pet_str, event_str))

    pet_classes = [all_pet_classes[x][1] for x in pet_class_indexes]
    event_class = all_event_classes[event_class_index][1]

    return pet_classes, event_class

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
    queue.put('/Users/elliotlevin/Temp/motion/dataset/motion.2021-02-04T18-32-03.mp4')
    video_processor(queue, {})