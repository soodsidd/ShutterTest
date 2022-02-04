from enum import IntEnum

class IOType(IntEnum):
    DIGITALINPUT=0
    DIGITALOUTPUT=1
    ANALOGINPUT=2
    ANALOGOUTPUT=3

class TempUnits(IntEnum):
    CELSIUS=0
    FARENHEIT=1
    KELVIN=2
    VOLTS=4
    NOSCALE=5