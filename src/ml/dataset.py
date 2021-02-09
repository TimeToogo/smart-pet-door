import sys
import os
import math
import json
import random
import tensorflow as tf
import numpy as np
import pprint
from .model import VideoClassifierModel
from .preprocess import preprocess_video
from ..config import config
from .class_map import reverse_class_map

VAL_PORTION = 0.1
TEST_PORTION = 0.1
BATCH_SIZE = 32
DATA_GENERATOR_VARIATIONS = 5

class VideoDataSequence(tf.keras.utils.Sequence):
    def __init__(self, labelled_vids, batch_size, datagen = False):
        self.labelled_vids = labelled_vids
        self.batch_size = batch_size
        self.cache = {}

        if datagen and DATA_GENERATOR_VARIATIONS:
            self.datagen = tf.keras.preprocessing.image.ImageDataGenerator(
                rotation_range=15,
                width_shift_range=0.1,
                height_shift_range=0.1,
                brightness_range=[0.5, 1.5],
                shear_range=0.2,
                zoom_range=0.25,
                fill_mode='constant',
                cval=0,
                horizontal_flip=True,
                vertical_flip=False,
            )
        else:
            self.datagen = None

    def genvids(self, amt, idx):
        vids = []

        if not self.datagen:
            batch = self.labelled_vids[idx * self.batch_size:(idx + 1) * self.batch_size]
            for item in batch:
                vid = preprocess_video(item['video'], cache=True)
                vids.append((vid, item['label']))
            
            return vids
        
        vid_index = math.floor(idx * self.batch_size / (1 + DATA_GENERATOR_VARIATIONS))
        variations_gen_index = (idx * self.batch_size) % (1 + DATA_GENERATOR_VARIATIONS)

        while len(vids) < amt:
            item = self.labelled_vids[vid_index]

            while variations_gen_index < DATA_GENERATOR_VARIATIONS + 1:
                vid = preprocess_video(item['video'], cache=True).copy()

                if variations_gen_index > 0:
                    transform = self.datagen.get_random_transform(vid.shape[1:])

                    frames, frame_h = vid.shape[:2]
                    for f in range(frames - 1):
                        vid[f:f+1] = self.datagen.apply_transform(vid[f:f+1].reshape(vid.shape[1:]), transform)

                    vid = vid / 255

                vids.append((vid, item['label']))
                variations_gen_index += 1

                if len(vids) == amt:
                    return vids

            vid_index = vid_index + 1 if vid_index < len(self.labelled_vids) - 1 else 0
            variations_gen_index = 0

        return vids

    def __len__(self):
        if self.datagen:
            return math.floor(len(self.labelled_vids) * (1 + DATA_GENERATOR_VARIATIONS) / self.batch_size)
        else:
            return math.ceil(len(self.labelled_vids) / self.batch_size)

    def __getitem__(self, idx):
        batch = self.genvids(self.batch_size, idx)

        batch_x = []
        batch_y = []

        for vid, label in batch:
            batch_x.append(vid)
            one_hot_class = self.parse_label(label)
            batch_y.append(one_hot_class)

        item = (np.array(batch_x), (np.array(batch_y)))

        return item

    def parse_label(self, label):
        one_hot_class = np.zeros(len(reverse_class_map), dtype='float32')

        if label == 'DISCARD':
            one_hot_class[reverse_class_map['DISCARD']] = 1.0
        else:
            pet_class = None

            for pet, _class in config.VC_PET_CLASSES.items():
                if pet in label:
                    pet_class = _class
                    break

            event_class = None
            for _event, _class in config.VC_EVENT_CLASSES.items():
                if label.endswith('_' + _event):
                    event_class = _class
                    break

            one_hot_class[reverse_class_map[str(pet_class) + '_' + str(event_class)]] = 1.0
            
        return one_hot_class
        
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

    summary = sorted(summary.items(), key=lambda x: x[1], reverse=True)

    print('summary:')
    pp = pprint.PrettyPrinter()
    pp.pprint(summary)

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
        'train': VideoDataSequence(train_vids, BATCH_SIZE, datagen=True),
    }

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    if len(sys.argv) < 2:
        print('usage: python -msrc.ml.dataset [label json path]')
        os.exit(1)

    dataset = load_dataset(sys.argv[1])

    if len(sys.argv) <= 2:
        for batch_x, batch_y in dataset['train']:
            plt.figure()
            f, axrr = plt.subplots(1, len(batch_x))
            for k, item in enumerate(batch_x):
                axrr[k].imshow(item.reshape((-1,) + item.shape[-2:]))
            plt.show()