import tensorflow as tf
from tensorflow.keras import layers as L
from ..config import config
from .class_map import class_map

class VideoClassifierModel(tf.keras.Model):
    def __init__(self):
        super().__init__()

        self.mobile_net = tf.keras.applications.MobileNetV2(
            input_shape=config.VC_INPUT_SHAPE[-3:],
            alpha=0.50,
            include_top=False,
            weights='imagenet'
        )

        self.td_mobile_net = L.TimeDistributed(self.mobile_net, name='time_distributed_mobile_net')
        self.td_mobile_net.trainable = False
        
        self.flatten1 = L.Reshape((config.VC_INPUT_SHAPE[0], -1))

        self.key_feature_extractor = L.TimeDistributed(L.Dense(64,  activation='relu'))
        self.batch_norm1 = L.BatchNormalization()
        self.dropout1 = L.Dropout(0.20)

        self.dense = L.Dense(32, activation='relu')
        self.batch_norm2 = L.BatchNormalization()
        self.dropout2 = L.Dropout(0.20)

        self.flatten2 = L.Reshape((-1,))

        self.event_class_output = L.Dense(len(class_map), activation='softmax', name="output_event")
    
    def call(self, inputs):
        x = inputs
        x = self.td_mobile_net(x)

        x = self.key_feature_extractor(x)
        x = self.batch_norm1(x)
        x = self.dropout1(x)
        x = self.flatten1(x)

        x = self.dense(x)
        x = self.batch_norm2(x)
        x = self.dropout2(x)

        x = self.flatten2(x)

        event = self.event_class_output(x)

        return event

    def model(self, input_shape):
        x = tf.keras.Input(shape=input_shape)
        return tf.keras.Model(inputs=[x], outputs=self.call(x))

                
if __name__ == '__main__':
    model = VideoClassifierModel().model(config.VC_INPUT_SHAPE)

    model.summary(line_length=130)
    print('output shape: ', model.output_shape)

