import numpy as np

class AMG8833:
    def __init__(self, **kwargs):
        pass

    def read_temp(self):
        return False, np.random.uniform(0.0, 4.0, (8,8))