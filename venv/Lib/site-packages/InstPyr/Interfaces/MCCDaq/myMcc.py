from mcculw import ul
from mcculw.device_info import DaqDeviceInfo
from mcculw.enums import *
from .console_examples_util import config_first_detected_device
from ..Common.interface import interface
from ..Common.inf_enums import *


class myMcc(interface):
    def __init__(self, device_detection=True):
        super().__init__(self)
        self._board_num=0
        self._dev_id_list=[]

        #always use device detection
        if device_detection:
            config_first_detected_device(self._board_num,self._dev_id_list)

        self.devinfo=DaqDeviceInfo(self._board_num)
        self.dio=self.devinfo.get_dio_info() if self.devinfo.supports_digital_io else None
        self.ai=self.devinfo.get_ai_info() if self.devinfo.supports_analog_input else None
        self.ao=self.devinfo.get_ao_info() if self.devinfo.supports_analog_output else None
        self.tc=self.devinfo.get_ai_info() if self.devinfo.supports_temp_input else None


    def initializeIO(self, din=[], dout=[], ain=[],
                     aout=[]):
        """Here din is a list of tuples of port and pin numbers """
        for pin in din:
            ul.d_config_bit(self._board_num,self.dio.port_info[pin[0]].type,pin[1],DigitalIODirection.IN)

        for pin in dout:
            ul.d_config_bit(self._board_num, self.dio.port_info[pin[0]].type, pin[1], DigitalIODirection.OUT)

        for pin in ain:
            pass
            # self.airange=self.ai.supported_ranges[0]
            #cofigure temperature channels here

    def configThermocouple(self,channel,type=0):
        # print(ul.get_config(InfoType.EXPANSIONINFO, self._board_num,channel,ExpansionInfo.THERMTYPE))
        ul.set_config(InfoType.BOARDINFO,self._board_num,channel,BoardInfo.CHANTCTYPE,TcType.K)
        # ul.set_config(InfoType.EXPANSIONINFO, self._board_num, channel, ExpansionInfo.THERMTYPE,
        #               TcType.K)



    def readTemperature(self,channel,units=TempUnits.CELSIUS):
        return ul.t_in(self._board_num, channel,units)


    def write_digital(self, pin, state):
        ul.d_bit_out(self._board_num,self.dio.port_info[pin[0]].type, pin[1],state)

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
