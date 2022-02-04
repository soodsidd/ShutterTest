from lakeshore import temperature_controllers
from ..Interfaces.Common import interface

import serial

class Lakeshore218_probe:
    def __init__(self,interface: interface.interface, channel):
        self.channel=channel
        self.interface=interface
        self.currentTemp=self.readTemperature()



    def readTemperature(self):
        self.currentTemp=self.interface.readTemperature(self.channel)
        return self.currentTemp


if __name__=='__main__':
    pass
    # probe=Lakeshore218_probe('COM8',1)
    # print(probe.readTemperature())

