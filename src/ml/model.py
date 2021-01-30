import tensorflow as tf
from tensorflow.keras import layers as L

# dims: frames, w, h, channels
INPUT_SHAPE = (15,64,64,1)
PET_CLASSES = {
    'Mia': 1,
    'Luna': 2,
    'Other': 3
}
EVENT_CLASSES = {
    'SIGHTING': 1,
    'WENT_INSIDE': 2,
    'WENT_OUTSIDE': 3,
    'HUNT': 4,
    'FIGHT': 5,
    'TOILET': 6,
    'OTHER': 7,
}

class VideoClassifierModel(tf.keras.Model):
    def __init__(self):
        super().__init__()

        self.td_conv1 = L.TimeDistributed(L.Conv2D(16, (2, 2), padding="same", activation="relu")) 
        self.max_pooling1 = L.TimeDistributed(L.MaxPooling2D((3, 3), strides=(3, 3)))
        self.td_conv2 = L.TimeDistributed(L.Conv2D(32, (2, 2), padding="same", activation="relu")) 
        self.max_pooling2 = L.TimeDistributed(L.MaxPooling2D((3, 3), strides=(3, 3)))
        self.td_conv3 = L.TimeDistributed(L.Conv2D(64, (2, 2), padding="same", activation="relu")) 
        self.max_pooling3 = L.TimeDistributed(L.MaxPooling2D((3, 3), strides=(3, 3)))
        self.flatten = L.Reshape((15, -1))
        self.lstm = L.LSTM(32)
        self.dense1 = L.Dense(256, activation='relu')
        self.pet_class_output = L.Dense(len(PET_CLASSES), activation='sigmoid')
        self.event_class_output = L.Dense(len(EVENT_CLASSES), activation='softmax')

    def call(self, inputs):
        x = inputs
        x = self.td_conv1(x)
        x = self.max_pooling1(x)
        x = self.td_conv2(x)
        x = self.max_pooling2(x)
        x = self.td_conv3(x)
        x = self.max_pooling3(x)
        x = self.flatten(x)
        x = self.lstm(x)
        x = self.dense1(x)
        pets = self.pet_class_output(x)
        event = self.event_class_output(x)

        return pets, event

    def model(self, input_shape):
        x = tf.keras.Input(shape=input_shape)
        return tf.keras.Model(inputs=[x], outputs=self.call(x))

if __name__ == '__main__':
    model = VideoClassifierModel().model(INPUT_SHAPE)

    model.summary(line_length=130)
    print('output shape: ', model.output_shape)

