import sys
import os
import math
import json
import random
import tensorflow as tf
import numpy as np
import pprint
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue
from time import sleep
from .model import VideoClassifierModel
from .preprocess import preprocess_video
from ..config import config
from .class_map import reverse_class_map

VAL_PORTION = 0.1
TEST_PORTION = 0.1
BATCH_SIZE = 32
ITEMS_PER_CLASS = 1000

class VideoDataSequence(tf.keras.utils.Sequence):
    def __init__(self, labelled_vids, batch_size, datagen = False):
        self.labelled_vids = labelled_vids
        self.batch_size = batch_size
        self.cache = {}

        if datagen and ITEMS_PER_CLASS:
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
            self.master_pool = ThreadPoolExecutor(max_workers=1)
            self.outstanding_threads = 0
            self.pool = ThreadPoolExecutor(max_workers=batch_size * 2)
            self.queue = Queue(batch_size * 10)
            self.balanced_labels = self.gen_balanced_data()
            self.master_pool.submit(self.gen_vids_bg)
            self.qsize = 0
            self.vid_cache = {}
        else:
            self.datagen = None

    def gen_balanced_data(self):
        grouped_by_class = {}
        balanced_labels = []

        for item in self.labelled_vids:
            if not item['label'] in grouped_by_class:
                grouped_by_class[item['label']] = []
            
            grouped_by_class[item['label']].append(item)

        for _class, items in grouped_by_class.items():
            variations_per_item = math.ceil(ITEMS_PER_CLASS / len(items))

            class_items = []
            for item in items:
                for i in range(variations_per_item):
                    transform = {'transform': i > 0}
                    class_items.append({**item, **transform})

                    if len(class_items) == ITEMS_PER_CLASS:
                        break
            
                if len(class_items) == ITEMS_PER_CLASS:
                    break

            for i in class_items:
                balanced_labels.append(i)

        random.Random(1).shuffle(balanced_labels)

        return balanced_labels

    def gen_vids_bg(self):
        try:
            while True:
                for idx in range(len(self)):
                    batch = self.balanced_labels[idx * self.batch_size:(idx + 1) * self.batch_size]

                    for item in batch:
                        self.pool.submit(self.gen_vid, item, self.datagen)
                        self.outstanding_threads += 1
                        while self.queue.full() or self.outstanding_threads > self.batch_size * 2:
                            sleep(0.01)
        except Exception as e:
            print(e)

    def gen_vid(self, item, datagen):
        if not item['video'] in self.vid_cache:
            self.vid_cache[item['video']] = preprocess_video(item['video'], cache=True).copy()

        vid = self.vid_cache[item['video']].copy()

        if item['transform']:
            transform = datagen.get_random_transform(vid.shape[1:])

            frames, frame_h = vid.shape[:2]
            for f in range(frames - 1):
                vid[f:f+1] = datagen.apply_transform(vid[f:f+1].reshape(vid.shape[1:]), transform)

            vid = vid / 255

        self.queue.put((vid, item['label']))
        self.outstanding_threads -= 1
        self.qsize += 1

    def genvids(self, amt, idx):
        vids = []

        if not self.datagen:
            batch = self.labelled_vids[idx * self.batch_size:(idx + 1) * self.batch_size]
            for item in batch:
                vid = preprocess_video(item['video'], cache=True)
                vids.append((vid, item['label']))
            
            return vids
        
        for i in range(amt):
            vids.append(self.queue.get(block=True))
            self.qsize -= 1

        return vids

    def __len__(self):
        if self.datagen:
            return math.ceil(len(self.balanced_labels) / self.batch_size)
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
        counts = np.zeros((len(reverse_class_map,)))
        for batch_x, batch_y in dataset['train']:
            plt.figure()
            f, axrr = plt.subplots(1, 8)
            counts[:np.max(np.argmax(batch_y, axis=1)) + 1] += np.bincount(np.argmax(batch_y, axis=1))
            print(counts)
            # for k in range(min(8, len(batch_x))):
            #     axrr[k].imshow(batch_x[k].reshape((-1,) + batch_x[k].shape[-2:]))
            
            # plt.show()