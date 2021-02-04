import tensorflow as tf
from tensorflow.keras import layers as L
from ..config import config

class TdConvBlock(tf.keras.layers.Layer):
    def __init__(self, filters):
        super().__init__()

        self.td_conv = L.TimeDistributed(L.Conv2D(filters, (2, 2), padding="same", activation='relu'))
        self.td_batch_norm = L.TimeDistributed(L.BatchNormalization())
        self.td_relu = L.TimeDistributed(L.Activation('relu'))
        self.td_pooling = L.TimeDistributed(L.MaxPooling2D((2, 2), strides=(2, 2)))

    def call(self, x):
        x = self.td_conv(x)
        x = self.td_batch_norm(x)
        x = self.td_relu(x)
        x = self.td_pooling(x)

        return x

class VideoClassifierModel(tf.keras.Model):
    def __init__(self):
        super().__init__()

        self.td_conv1 = TdConvBlock(16)
        self.td_conv2 = TdConvBlock(32)
        self.td_conv3 = TdConvBlock(64)
        self.td_conv4 = TdConvBlock(128)
        self.flatten = L.Reshape((15, -1))
        self.lstm = L.LSTM(32)
        self.dense1 = L.Dense(256, activation='relu')
        self.dropout1 = L.Dropout(0.5)
        self.pet_class_output = L.Dense(len(config.VC_PET_CLASSES), activation='sigmoid', name="output_pets")
        self.event_class_output = L.Dense(len(config.VC_EVENT_CLASSES), activation='softmax', name="output_event")
    
    def call(self, inputs):
        x = inputs
        x = self.td_conv1(x)
        x = self.td_conv2(x)
        x = self.td_conv3(x)
        x = self.td_conv4(x)
        x = self.flatten(x)
        x = self.lstm(x)
        x = self.dense1(x)
        x = self.dropout1(x)
        pets = self.pet_class_output(x)
        event = self.event_class_output(x)

        return pets, event

    def model(self, input_shape):
        x = tf.keras.Input(shape=input_shape)
        return tf.keras.Model(inputs=[x], outputs=self.call(x))

if __name__ == '__main__':
    model = VideoClassifierModel().model(config.VC_INPUT_SHAPE)

    model.summary(line_length=130)
    print('output shape: ', model.output_shape)

