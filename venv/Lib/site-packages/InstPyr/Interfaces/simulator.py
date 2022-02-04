
from .Common.interface import interface
from .Common.inf_enums import *
import numpy as np

class simulator(interface):
    def __init__(self, device_detection=True):
        super().__init__(self)


        #always use device detection



    def initializeIO(self, din=[], dout=[], ain=[],
                     aout=[]):
        """Here din is a list of tuples of port and pin numbers """
        pass


    def configThermocouple(self,channel,type=0):
        pass




    def readTemperature(self,channel,units=TempUnits.CELSIUS):
        return 105-5*np.random.random()


    def write_digital(self, pin, state):
        pass

    def read_analog(self, pin):
        pass

    def read_digital(self, pin):
        pass

    def write_analog(self, pin, pwmvalue):
        pass




if __name__=="__main__":
    mccdev=myMcc()
    mccdev.initializeIO(dout=[[0,2]])
    # mccdev.write_digital([0,2],True)
    print(mccdev.readTemperature(1,TempUnits.CELSIUS))
