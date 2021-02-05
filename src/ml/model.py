import tensorflow as tf
from tensorflow.keras import layers as L
from ..config import config

class VideoClassifierModel(tf.keras.Model):
    def __init__(self):
        super().__init__()

        self.td_mobile_net = L.TimeDistributed(tf.keras.applications.MobileNetV2(
            input_shape=config.VC_INPUT_SHAPE[-3:],
            alpha=0.35,
            include_top=False,
            weights='imagenet'
        ), name='time_distributed_mobile_net')
        self.td_mobile_net.trainable = False

        self.flatten = L.Reshape((config.VC_INPUT_SHAPE[0], -1))
        self.lstm = L.LSTM(32)
        self.dense1 = L.Dense(256, activation='relu')
        self.dropout1 = L.Dropout(0.5)
        self.pet_class_output = L.Dense(len(config.VC_PET_CLASSES), activation='sigmoid', name="output_pets")
        self.event_class_output = L.Dense(len(config.VC_EVENT_CLASSES), activation='softmax', name="output_event")
    
    def call(self, inputs):
        x = inputs
        x = self.td_mobile_net(x)
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

