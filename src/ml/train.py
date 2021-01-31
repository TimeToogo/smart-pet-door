import sys
import math
import json
import random
import tensorflow as tf
import numpy as np
from .model import VideoClassifierModel
from .preprocess import preprocess_video
from ..config import config

if len(sys.argv) < 3:
    print('usage: python -msrc.ml.train [labels json file] [saved model dir]')
    sys.exit(1)

BATCH_SIZE = 8
VAL_PORTION = 0.1
TEST_PORTION = 0.1

EPOCHS = 40
LEARNING_RATE = 1e-4

class VideoDataSequence(tf.keras.utils.Sequence):
    def __init__(self, labelled_vids, batch_size):
        self.labelled_vids = labelled_vids
        self.batch_size = batch_size
        self.cache = {}

    def __len__(self):
        return math.ceil(len(self.labelled_vids) / self.batch_size)

    def __getitem__(self, idx):
        if idx in self.cache:
            return self.cache[idx]

        batch = self.labelled_vids[idx * self.batch_size:(idx + 1) * self.batch_size]

        batch_x = []
        batch_y_pets = []
        batch_y_event = []

        for item in batch:
            batch_x.append(preprocess_video(item['video']))
            pets, event = self.parse_label(item['label'])
            batch_y_pets.append(pets)
            batch_y_event.append(event)

        item = (np.array(batch_x), (np.array(batch_y_pets), np.array(batch_y_event)))
        self.cache[idx] = item

        return item

    def parse_label(self, label):
        pets = np.zeros(len(config.VC_PET_CLASSES), dtype='float32')
        event = np.zeros(len(config.VC_EVENT_CLASSES), dtype='float32')

        if label == 'DISCARD':
            pets[config.VC_PET_CLASSES['NOT_PET'] - 1] = 1.0
            event[config.VC_EVENT_CLASSES['DISCARD'] - 1] = 1.0
        else:
            for pet, _class in config.VC_PET_CLASSES.items():
                if pet in label:
                    pets[_class - 1] = 1.0
                
            for _event, _class in config.VC_EVENT_CLASSES.items():
                if label.endswith('_' + _event):
                    event[_class - 1] = 1.0

        return (pets, event)
        
def load_dataset(json_path):
    print('loading dataset from %s' % json_path)
    labelled_vids = json.load(open(json_path, 'r'))

    print('loaded %d items' % len(labelled_vids))
    
    summary = {}
    for item in labelled_vids:
        if not item['label'] in summary:
            summary[item['label']] = 1
        else:
            summary[item['label']] += 1

    print('summary:')
    print(str(summary))

    SEED = 1
    random.Random(SEED).shuffle(labelled_vids)

    val_amt = math.floor(len(labelled_vids) * VAL_PORTION)
    test_amt = math.floor(len(labelled_vids) * TEST_PORTION)

    val_vids = labelled_vids[:val_amt]
    test_vids = labelled_vids[val_amt:val_amt+test_amt]
    train_vids = labelled_vids[val_amt+test_amt:]

    print('train amt: ', len(train_vids))
    print('val amt: ', len(val_vids))
    print('test amt: ', len(test_vids))

    return {
        'val': VideoDataSequence(val_vids, BATCH_SIZE),
        'test': VideoDataSequence(test_vids, BATCH_SIZE),
        'train': VideoDataSequence(train_vids, BATCH_SIZE),
    }

def train_model(dataset):
    print('loading model')
    model = VideoClassifierModel()

    model.compile(optimizer=tf.keras.optimizers.Adam(LEARNING_RATE), loss=['categorical_crossentropy'] * 2, metrics=['accuracy'])
    
    print('training model')
    model.fit(dataset['train'], validation_data=dataset['val'], epochs=EPOCHS)

    print('evaluating model')
    model.evaluate(dataset['test'])

    return model

def save_model(model, path):
    print('saving model to %s' % path)

    model.save(path + '/saved_model/')

    print('creating tflite model')
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    with open(path + '/model.tflite', 'wb') as f:
        f.write(tflite_model)

if __name__ == '__main__':
    dataset = load_dataset(sys.argv[1])
    model = train_model(dataset)
    save_model(model, sys.argv[2])
    print('done')