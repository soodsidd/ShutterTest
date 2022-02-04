from ..Interfaces.Common import interface,inf_enums
class thermocouple():
    def __init__(self,interface:interface.interface,pins, type='k', units=inf_enums.TempUnits.CELSIUS):
        self.interface=interface
        self.interface.initializeIO(ain=[pins])
        self.pins=pins
        self.type=type
        self.currentTemp=0
        if(self.interface.configThermocouple(pins,type)==None):
            self.config(type)
        self.units=units

    def readTemperature(self):
        self.currentTemp=round((self.interface.readTemperature(self.pins,self.units)),3)
        if(self.currentTemp==None):
            return self.calcTemp()
        else:
            return self.currentTemp

    def config(self,type):
        pass

    def calcTemp(self):
        pass


