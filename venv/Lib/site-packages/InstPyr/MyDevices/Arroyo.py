import serial, time
import numpy as np
import pyvisa as visa
from numpy import array, savetxt
from dataclasses import dataclass

@dataclass
class CommandList:
    CURRENT_SET:str='I_set'
    PHOTODIODE:str='P'
    CURRENT:str='I'
    VOLTAGE:str='V'
    TEMP_SET:str='T_set'
    TEMP:str='T'
    CURRENT_TEC:str='I_TEC'
    VOLTAGE_TEC:str='V_TEC'


class myArroyo():
    def __init__(self, portNo = 'COM4', rate = 38400) -> None:
        # SERIAL CONNECTION TO ARROYO 6305
        self.ser = serial.Serial(port = portNo,\
                            baudrate = rate,\
                            parity = serial.PARITY_NONE,\
                            stopbits = serial.STOPBITS_ONE,\
                            bytesize = serial.EIGHTBITS,\
                            timeout = 1,\
                            xonxoff = False,\
                            rtscts = False,\
                            dsrdtr = False)

    def __del__(self):
        self.ser.close()
        print('Serial port is closed.')


    def get_param(self, par):
        ser = self.ser
        if par == 'I_set': # read laser current set value
            ser.write(b'LAS:SET:LDI?\r\n')
        elif par == 'P': # read monitor photodiode
            ser.write(b'LAS:MDP?\r\n')
        elif par == 'I': # read laser current process value
            ser.write(b'LAS:LDI?\r\n')
        elif par == 'V': # read laser voltage
            ser.write(b'LAS:LDV?\r\n')
        elif par == 'T_set': # read temperature set value
            ser.write(b'TEC:SET:T?\r\n')
        elif par == 'T': # read temperature process value
            ser.write(b'TEC:T?\r\n')
        elif par == 'I_TEC': # read TEC current
            ser.write(b'TEC:ITE?\r\n')
        elif par == 'V_TEC': # read TEC voltage
            ser.write(b'TEC:V?\r\n')
        l1 = str(ser.readline())
        l2 = str(ser.readline())
        return float(l1[2:-5])

    def set_param(self, par, value):
        ser = self.ser
        if par == 'I_set': # set laser current
            s = 'LAS:LDI ' + str(value) + '\r\n'
            ser.write(s.encode('UTF-8'))
        elif par == 'T_set': # set laser temperature
            s = 'TEC:T ' + str(value) + '\r\n'
            ser.write(s.encode('UTF-8'))