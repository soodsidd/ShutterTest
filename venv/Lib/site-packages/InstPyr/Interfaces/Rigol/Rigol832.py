import sys
import pyvisa
from ..Common.interface import  interface
from visa import *
import time

_delay=0.01

class Rigol832(interface):
    def __init__(self):
        super().__init__(self)
        self.analogmode='CV'
        self.currentchannel=1
        try:
            self.rm=pyvisa.ResourceManager()
            self.instrument_list=self.rm.list_resources()
            print(self.instrument_list)
            self.address=[elem for elem in self.instrument_list if (elem.find('USB')!=-1) and elem.find('DP')!=-1]
            if self.address.__len__() == 0:
                self.status = "Not Connected"
                # print("Could not connect to device")
            else:
                self.address = self.address[0]
                self.device = self.rm.open_resource(self.address)
                print("Connected to " + self.address)
                self.status = "Connected"
                self.connected_with = 'USB'

        except VisaIOError:
            print('Instrument not found')
        self.initializeIO()



    def initializeIO(self, din=[], dout=[], ain=[],
                     aout=[]):
        for i in range(3):
            self.setOCP(i+1,False)
            self.setOVP(i+1,False)
            self.write_digital(i+1,0)


    def write_digital(self, channel, state):
        outputstate='ON' if state==1 else 'OFF'
        command=':OUTP CH%s, %s'%(channel,outputstate)
        print(command)
        self.device.write(command)
        time.sleep(_delay)

    def read_digital(self, channel):
        command=':OUTP? CH%s'%channel
        return self.device.query(command).rstrip()

    def write_analog(self, channel,current=0.0,voltage=0.0,mode=''):
        #TODO change this enum
        if mode !='':
            self.analogmode=mode
        if self.analogmode=='CC':
            self.setCurrent(channel,current)
        elif self.analogmode=='CV':
            self.setVoltage(channel, voltage)
        if self.read_digital(channel)=='OFF':
            self.write_digital(channel,1)




    def setDigitalVoltage(self, voltage, channel=1,currentlim=0.0):
        if currentlim==0:
            command=':APPL Ch%s,%s'%(channel,voltage)
        else:
            command=':APPL Ch%s,%s,%s'%(channel,voltage,currentlim)
        self.device.write(command)
        time.sleep(_delay)

    def getCurrent(self,channel):
        command=':MEAS:CURR? CH%s'%(channel)
        return self.device.query(command)

    def getVoltage(self,channel):
        command=':MEAS:VOLT? CH%s'%(channel)
        return self.device.query(command)

    def getPower(self,channel):
        command=':MEAS:POWE? CH%s'%(channel)
        return self.device.query(command)

    def setCurrent(self,channel,current):
        # command=':INST:NSEL %s'%(channel)
        command = ':APPL Ch%s,,%s' % (channel, current)
        self.device.write(command)
        time.sleep(_delay)
        # command=':CURR %s'%current
        # time.sleep(_delay)

    def setVoltage(self,channel,voltage):
        # command = ':INST:NSEL %s' % (channel)
        # self.device.write(command)
        command=':APPL Ch%s,%s'%(channel,voltage)
        time.sleep(_delay)
        # command = ':VOLT %s' % voltage
        self.device.write(command)
        time.sleep(_delay)

    def setCurrentLim(self,currentlim,channel=0):
        if channel==0:
            for i in range(3):
                command=':OUTP:OCP:VAL CH%s,%s'%(i+1,currentlim)
                time.sleep(_delay)
                self.device.write(command)
                self.setOCP(i+1,True)

        else:
            command=':OUTP:OCP:VAL CH%s,%s'%(channel,currentlim)
            time.sleep(_delay)
            self.device.write(command)
            self.setOCP(channel,True)

    def setOCP(self,channel,state):
        st='ON' if state==True else 'OFF'
        command = 'OUTP:OCP CH%s,%s' % (channel,st)
        time.sleep(_delay)
        self.device.write(command)

    def setOVP(self, channel, state):
        st = 'ON' if state == True else 'OFF'
        command = 'OUTP:OVP CH%s,%s' % (channel, st)
        time.sleep(_delay)
        self.device.write(command)

    def setVoltageLim(self,voltagelim,channel=0):
        if channel==0:
            for i in range(3):
                command=':OUTP:OVP:VAL CH%s,%s'%(i+1,voltagelim)
                time.sleep(_delay)
                self.device.write(command)
                self.setOVP(i+1,True)
        else:
            command=':OUTP:OVP:VAL CH%s,%s'%(channel,voltagelim)
            time.sleep(_delay)
            self.device.write(command)
            self.setOVP(channel,True)

    def disableoutputs(self):
        self.write_digital(1,0)
        self.write_digital(2,0)
        self.write_digital(3,0)

    def shutdown(self):
        self.disableoutputs()




if __name__=='__main__':
    mydevice=Rigol832()
    mydevice.setDigitalVoltage(10,1)
    mydevice.write_digital(1,1)


