import sys
import os
import math
import json
import random
import tensorflow as tf
import numpy as np
from .model import VideoClassifierModel
from .preprocess import preprocess_video
from ..config import config
from .class_map import reverse_class_map
from .dataset import VideoDataSequence, load_dataset

if len(sys.argv) < 3:
    print('usage: python -msrc.ml.train [labels json file] [saved model dir]')
    sys.exit(1)

EPOCHS = 40
LEARNING_RATE = 1e-4

def train_model(dataset):
    print('loading model')
    model = VideoClassifierModel()

    model.compile(optimizer=tf.keras.optimizers.Adam(LEARNING_RATE), loss=['categorical_crossentropy'], metrics=['accuracy'])
    
    print('training model')
    model.fit(dataset['train'], validation_data=dataset['val'], epochs=EPOCHS)

    print('evaluating model')
    model.evaluate(dataset['test'])

    return model

def save_model(model, path):
    print('saving model to %s' % path)

    os.makedirs(path, exist_ok=True)
    model.save_weights(path + '/saved_model.h5')

    print('creating tflite model')
    unbatched_model = VideoClassifierModel().model(config.VC_INPUT_SHAPE)
    unbatched_model.set_weights(model.get_weights())
    converter = tf.lite.TFLiteConverter.from_keras_model(unbatched_model)
    tflite_model = converter.convert()

    with open(path + '/model.tflite', 'wb') as f:
        f.write(tflite_model)

if __name__ == '__main__':
    dataset = load_dataset(sys.argv[1])
    model = train_model(dataset)
    save_model(model, sys.argv[2])
    print('done')