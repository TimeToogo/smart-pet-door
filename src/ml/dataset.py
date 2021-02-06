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
BATCH_SIZE = 4

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
        batch_y = []

        for item in batch:
            batch_x.append(preprocess_video(item['video'], cache=True))
            one_hot_class = self.parse_label(item['label'])
            batch_y.append(one_hot_class)

        item = (np.array(batch_x), (np.array(batch_y)))
        self.cache[idx] = item

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
        'train': VideoDataSequence(train_vids, BATCH_SIZE),
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python -msrc.ml.dataset [label json path]')
        os.exit(1)

    load_dataset(sys.argv[1])