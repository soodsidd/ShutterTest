import numpy as np

class Noise:
    def __init__(self):
        pass

    @classmethod
    def generate(cls,max=1):
        while True:
            temp=np.random.random()*max
            yield temp


if __name__=="__main__":
    while True:
        print(next(Noise.generate(2)))
