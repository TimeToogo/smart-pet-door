import sys
import os
import math
import json
import random
import tensorflow as tf
import numpy as np
from .preprocess import preprocess_video
from .model import VideoClassifierModel
from ..config import config

def load_keras_model():
    model_path = os.path.dirname(config.VP_TFLITE_MODEL_PATH) + '/saved_model.h5'
    config.logger.info('loading keras model from %s' % model_path)
    model = VideoClassifierModel()
    model.build((1,) + config.VC_INPUT_SHAPE)
    model.load_weights(model_path)

    return model

def load_tflite_model():
    config.logger.info('loading tflite model from %s' % config.VP_TFLITE_MODEL_PATH)
    interpreter = tf.lite.Interpreter(model_path=config.VP_TFLITE_MODEL_PATH)
    interpreter.allocate_tensors()
    config.logger.info('loaded model')

    return interpreter

if __name__ == '__main__':
    keras_model = load_keras_model()
    tflite_model = load_tflite_model()

    eval_data = {
        'MIA': '/Users/elliotlevin/Temp/motion/dataset/motion.2021-02-04T18-32-03.mp4',
        'LUNA': '/Users/elliotlevin/Downloads/16cef8c3-76f1-40d9-acbd-228252695182.mp4',
        'DISCARD': '/Users/elliotlevin/Temp/motion/dataset/motion.2021-02-04T14-11-59.mp4'
    }

    for name, video in eval_data.items():
        print('================================')
        print('running test [%s]' % name)
        video = preprocess_video(video)
        video = video.reshape((1,) + video.shape)

        print('keras output:', keras_model.predict(video))

        input_details = tflite_model.get_input_details()
        tensor_index = tflite_model.get_input_details()[0]['index']
        tflite_model.set_tensor(input_details[0]['index'], video)

        tflite_model.invoke()

        output_details = tflite_model.get_output_details()
        results = tflite_model.get_tensor(output_details[0]['index'])

        print('tflite output:', results)

    