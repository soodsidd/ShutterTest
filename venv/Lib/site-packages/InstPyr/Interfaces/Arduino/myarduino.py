import pyfirmata
from ..Common.interface import interface
from ..Common.inf_enums import *


class myarduino(interface):
    def __init__(self,port, readenable=False):
        super().__init__(self)
        self.board=pyfirmata.Arduino(port)
        it=pyfirmata.util.Iterator(self.board)
        it.start()


    def initializeIO(self,din=[],dout=[],ain=[],
                     aout=[]):

        #TODO refactor

        for pin in din:
            self.board.digital[pin].mode=pyfirmata.INPUT

        for pin in dout:
            self.board.digital[pin].mode=pyfirmata.OUTPUT

        for pin in ain:
            self.board.analog[pin].enable_reporting()

        for pin in aout:
            self.board.analog[pin].mode=pyfirmata.PWM



    def write_digital(self,pin,state,voltage=5):
        self.board.digital[pin].write(state)

    def read_digital(self,pin):
        return self.board.digital[pin].read()

    def read_analog(self,pin):
        return self.board.analog[pin].read()

    def write_analog(self,pin,pwmvalue):
        self.board.digital[pin].write(pwmvalue)

if __name__=='__main__':
    import time

    arduino=myarduino('COM3')
    arduino.initializeIO(aout=[3])
    #TODO convert the modes above to struct or typedef
    counter=0.01
    rampup=True
    while(True):
        arduino.write_analog(3,counter)
        if counter<=0.99 and rampup:
            counter+=0.01
        elif counter>0.99 and rampup:
            rampup=False
        elif counter>=0.01 and not rampup:
            counter-=0.01
        elif counter<0.01 and not rampup:
            rampup=True

        time.sleep(0.1)

        # arduino.write_digital(13,0)
        # print(arduino.read_digital(7))
        # time.sleep(1)
        # arduino.write_digital(13,1)
        # print(arduino.read_digital(7))
        # print(arduino.read_analog(0))
        # time.sleep(1)









