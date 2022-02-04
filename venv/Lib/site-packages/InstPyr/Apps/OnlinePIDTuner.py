from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import *
from PyQt5 import QtCore
import sys
# from Logging import Logger
from src.InstPyr.UI import mainpanel_control
from queue import Queue
from datetime import datetime
# from Plotting import Plotter
# from Interfaces.MCCDaq import myMcc
# from Interfaces.simulator import simulator
# import MyDevices.thermocouple as thermocouple
# from Control.Sensor import MySensor
# from Control.Filter import MyFilter
# from MyDevices.helpers import *
import time
import src.InstPyr.Interfaces.simulator as simulator
# from src.InstPyr.Control.Sensor import MySensor
from src.InstPyr.Control.Filter import MyFilter
from src.InstPyr.Control import PID,Plant,Waveform
from src.InstPyr.MyDevices.thermocouple import thermocouple
from src.InstPyr.Plotting import Plotter
from src.InstPyr.Logging import Logger
from src.InstPyr.Utilities import watch
from src.InstPyr.MyDevices.Lakeshore_probe import Lakeshore218_probe
from varname import nameof

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)

class MainWindow(QMainWindow,mainpanel_control.Ui_MainWindow):
    statusmsg = pyqtSignal(str, name='statusmsg')
    def __init__(self):
        super(self.__class__,self).__init__()
        self.setupUi(self)
        self.checkboxcount=0

        # self.formLayout.addWidget(self.checkbox3)

        #setup interface and devices
        # self.interface=myMcc.myMcc()
        # self.motor=Plant.Plant([6954154,179],[49370544,71435,1])
        # self.motor=Plant.Plant([1,1],[1,0.5,0.5,1])

        self.motor=Plant.Plant([1],[100,1])
        # self.motor=Plant.Plant([1],[1,0.5,1])
        self.interface=simulator.simulator()

        #create a simulated system based on a transfer function

        self.pidcontroller=PID.PID(self.Kp.value(),self.Kp.value()/self.Ti.value(),self.Kp.value()*self.Td.value(),out_min=self.Minout.value(),out_max=self.Maxout.value()) #unbounded PID


        self.sensors={}
        self.var_checkboxes=[]

        #variables
        self.logger = None
        self.buffersize = 1000# self.Buffersize.value()
        self.samplingrate = 500  # int(1000/self.Sampling.value())
        self.logfilename = ''
        self.logEnable = False

        #control variables
        self.currentTime=0
        self.motoroutput=0
        self.setpoint=self.Setpoint.value()
        self.error=0
        self.controlsignal=0
        self.P=0
        self.I=0
        self.D=0
        self.squarewave=Waveform.square(self.samplingrate/1000,30,5,-5)
        self.osc_setpoint=False
        self.PIDAutotuner=None
        self.minout=self.Minout.value()
        self.maxout=self.Maxout.value()
        self.ATstatus=None
        self.ATmethod=PID.MethodList.TL_PI

        #sensors
        self.sensors['output_k']=watch.watch('Motor output',nameof(self.motoroutput),callfunc=self.variableProbe)
        self.sensors['setpoint_k'] = watch.watch('Setpoint', nameof(self.setpoint), callfunc=self.variableProbe)
        self.sensors['error_k'] = watch.watch('Error signal', nameof(self.error), callfunc=self.variableProbe)
        self.sensors['controlsignal_k']=watch.watch('Control Signal',nameof(self.controlsignal),callfunc=self.variableProbe)
        self.sensors['P_k']=watch.watch('P contribution',nameof(self.P),callfunc=self.variableProbe)
        self.sensors['I_k']=watch.watch('I contribution',nameof(self.I),callfunc=self.variableProbe)
        self.sensors['D_k']=watch.watch('D contribution',nameof(self.D),callfunc=self.variableProbe)

        self.mainplotvars=['output_k','setpoint_k','error_k']
        self.controlplotvars=['controlsignal_k','P_k','I_k','D_k']

        # self.sensors['controlsignal']=watch.watch('Control Signal',nameof(self.controlsignal),callfunc=self.variableProbe)


        #setup widgets
        self.mainplot=Plotter.MyPlotter(self.Mainplot, initdata={self.sensors[x].name:[] for x in self.mainplotvars},buffersize=10000,oneaxis=True,datetimeaxis=False)
        self.controlplot=Plotter.MyPlotter(self.Controlplot, initdata={self.sensors[x].name:[] for x in self.controlplotvars},buffersize=10000,oneaxis=True,datetimeaxis=False)



        for key in self.sensors.keys():
            self.var_checkboxes+=[self.addCheckbox(self.sensors[key].name,key)]
        self.statusmsg.connect(self.eventHandler)



        #setup threads
        self.threadpool=QThreadPool()
        self.dispQueue=Queue()
        dispWorker=Worker(self.update_display)
        self.threadpool.start(dispWorker)

        self.logQueue = Queue()
        logWorker = Worker(self.logdata)
        self.threadpool.start(logWorker)

        self.eventQueue=Queue()
        # print(self.var_checkboxes)

        self.timer=QtCore.QTimer()
        self.timer.setInterval(self.samplingrate)
        self.timer.timeout.connect(self.mainloop)
        self.timer.start()
        self.logQueue.join()
        self.dispQueue.join()

    def mainloop(self):
        self.currentTime+=self.samplingrate/1000
        self.motoroutput=self.motor.realTime(self.controlsignal,self.currentTime)
        if self.osc_setpoint:
            self.setpoint=self.squarewave.nextval()
        self.error=self.setpoint-self.motoroutput
        self.controlsignal = self.pidcontroller.apply(self.error, self.currentTime)
        self.P = self.pidcontroller.P
        self.I = self.pidcontroller.I
        self.D = self.pidcontroller.D
        if self.PIDAutotuner is not None:
            control, self.ATstatus = self.PIDAutotuner.nextVal(self.motoroutput, self.controlsignal)

            if self.ATstatus==PID.TuningStatus.COARSE_SETTLING:
                pass
            elif self.ATstatus==PID.TuningStatus.COARSE_READY or self.ATstatus==PID.TuningStatus.FINE_READY:
                params = self.PIDAutotuner.PIDparameters()
                self.Kp.setValue(params['Kc'])
                self.Ti.setValue(params['Ti'])
                self.Td.setValue(params['Td'])
                self.pidcontroller = PID.PID(params['Kc'], params['Kc'] / params['Ti'], params['Kc'] * params['Td'],
                                             out_min=self.minout, out_max=self.maxout)
                self.setpoint = self.autotuneSetpoint.value()

                if self.ATstatus==PID.TuningStatus.FINE_READY:
                    self.AutotuneEnable.setText('Autotune!')
                    self.AutotuneEnable.setChecked(False)
                    self.PIDAutotuner = None
                    self.autoTuneUI_update(False)

            elif self.ATstatus==PID.TuningStatus.COARSE_RELAY or self.ATstatus==PID.TuningStatus.FINE_RELAY:
                self.controlsignal=control

            elif self.ATstatus==PID.TuningStatus.DWELL:
                self.controlsignal=control

        print(self.ATstatus)





        data={}
        for key in self.sensors.keys():
            data[self.sensors[key].name]=[self.currentTime,self.sensors[key].read()]
        self.dispQueue.put(data)
        logdata=[datetime.now()]+[x.read() for x in self.sensors.values()]

        if self.logEnable:
            try:
                event = self.eventQueue.get(timeout=0.1)
                self.logQueue.put(logdata + [event])
            except Exception:
                self.logQueue.put(logdata)



    def update_display(self):
        while(True):
            data=self.dispQueue.get(timeout=1000)
            #data is a dictionary
            self.dispQueue.task_done()
            mainplotarray=[self.sensors[x].name for x in self.mainplotvars]
            controlplotarray=[self.sensors[x].name for x in self.controlplotvars]
            for key in data.keys():
                if key in mainplotarray:
                    self.mainplot.updatedata({key:data[key]})
                elif key in controlplotarray:
                    self.controlplot.updatedata({key:data[key]})
            self.mainplot.redraw()
            self.controlplot.redraw()

    def logdata(self):
        while True:
            data = self.logQueue.get()
            self.logQueue.task_done()
            if self.logger is not None and self.logEnable:
                self.logger.writetimedata(data)



    def eventHandler(self,*args):
        name=self.sender().objectName()
        print(name)
        if name=="logenable":
            self.logEnable=self.logenable.isChecked()
            if self.logEnable is True and self.filename.toPlainText() != '':
                if self.logger is not None:
                    #if filename is new, create new logger
                    # print(self.logger.fname)
                    # print(self.filename.toPlainText())
                    if self.logger.fname != self.filename.toPlainText():
                        #close previous file
                        self.logger.close()
                        try:
                            self.logger=Logger.Logger(self.filename.toPlainText(),[x.name for x in self.sensors.values()],'w+')
                            self.statusmsg.emit('Recording')
                        except Exception:
                            self.logger=None
                            self.statusmsg.emit('File already exists')
                            self.logenable.setChecked(False)

                    else:
                        while not self.logQueue.empty():
                            try:
                                self.logQueue.get(False)
                            except Exception:
                                continue
                            self.logQueue.task_done()
                        self.logger = Logger.Logger(self.filename.toPlainText(),
                                                    [x.name for x in self.sensors.values()], 'a')
                        self.statusmsg.emit('Recording')

                else:
                    try:
                        self.logger = Logger.Logger(self.filename.toPlainText(), [x.name for x in self.sensors.values()],'w+')
                        self.statusmsg.emit('Recording')
                    except Exception:
                        self.logger=None
                        self.statusmsg.emit('File already exists')
                        self.logenable.setChecked(False)



            elif self.logEnable is False:
                self.statusmsg.emit('')
                if self.logger is not None:
                    self.logger.close()
        if name=='Buffersize':
            self.mainplot.buffer=int(self.Buffersize.value()*self.Sampling.value())
            self.controlplot.buffer=int(self.Buffersize.value()*self.Sampling.value())

            self.statusmsg.emit('Changed show last')
        if name=='Sampling':
            # self.timer.stop()
            self.timer.setInterval(int(1000/self.Sampling.value()))
            # self.statusmsg.emit('Changed sampling rate')
        if name=='clear':
            self.mainplot.clear()
            self.controlplot.clear()
        if name=='MainWindow':
            self.statusbar_2.setText(args[0])
        if name=='annotate':
            self.plot.annotate(self.annotatemsg.toPlainText())
            if self.logEnable:
                #construct blank data:
                self.eventQueue.put(self.annotatemsg.toPlainText())
            self.annotatemsg.setText('')

        if name=='horZoom':
            self.mainplot.buffer=int(10000*self.horZoom.value()/100)
            self.controlplot.buffer=int(10000*self.horZoom.value()/100)

            print(self.mainplot.buffer)

        if name=='Setpoint':
            self.setpoint=self.Setpoint.value()
            print(self.setpoint)

        if name=='Kp':
            self.pidcontroller.Kp=self.Kp.value()

        if name=='Ti':
            try:
                self.pidcontroller.Ki=self.Kp.value()/self.Ti.value()
            except Exception:
                print('bad Ti value')

        if name=='Td':
            self.pidcontroller.Kd=self.Kp.value()*self.Td.value()

        if name=='Maxout':
            self.pidcontroller.outmax=self.Maxout.value()
            self.maxout=self.Maxout.value()

        if name=='Minout':
            self.pidcontroller.outmin=self.Minout.value()
            self.minout=self.Minout.value()

        if name=='squaregen':
            if self.squaregen.isChecked():
                self.squarewave=Waveform.square(self.samplingrate/1000,self.squareperiod.value(),
                                                self.squareamp.value(),
                                                -self.squareamp.value())
                self.squaregen.setText('Stop')
                self.osc_setpoint=True
            else:
                self.squaregen.setText('Generate')
                self.osc_setpoint=False

        if name=='AutotuneMethod':
            kp=self.Kp.value()
            Ti=self.Ti.value()
            Td=self.Td.value()
            newmethod=self.AutotuneMethod.currentIndex()
            params=PID.PIDAutotuneRT.convertPID(kp,Ti,Td,self.ATmethod,newmethod)
            self.ATmethod=newmethod
            self.Kp.setValue(params['Kp'])
            self.Ti.setValue(params['Ti'])
            self.Td.setValue(params['Td'])
            self.pidcontroller.Kp=params['Kp']
            self.pidcontroller.Ti=params['Ti']
            self.pidcontroller.Td=params['Td']

        if name=='AutotuneEnable':
            if self.AutotuneEnable.isChecked():
                self.PIDAutotuner=PID.PIDAutotuneRT(self.autotuneSetpoint.value(),self.autotuneControlAmp.value(),self.autotuneControlFineAmp.value(), cycles=self.autotuneCycles.value(),method=self.AutotuneMethod.currentIndex())
                self.ATmethod=self.AutotuneMethod.currentIndex()
                self.AutotuneEnable.setText('Autotuning')
                self.ATstatus=PID.TuningStatus.COARSE_RELAY
                self.autoTuneUI_update(True)
            else:
                self.PIDAutotuner=None
                self.AutotuneEnable.setText('Autotune!')
                self.ATstatus=0
                self.autoTuneUI_update(False)

        if name in self.var_checkboxes:
            mainplotarray = [self.sensors[x].name for x in self.mainplotvars]
            controlplotarray = [self.sensors[x].name for x in self.controlplotvars]
            exec("self.cname=self."+name)
            # print(name)
            # dispname=self.skbot.text()
            if self.cname.text() in mainplotarray:
                if self.cname.isChecked():
                    self.mainplot.show(self.cname.text())
                else:
                    self.mainplot.hide(self.cname.text())
            elif self.cname.text() in controlplotarray:
                if self.cname.isChecked():
                    self.controlplot.show(self.cname.text())
                else:
                    self.controlplot.hide(self.cname.text())
            # pass

            #TODO - annotate at any timestamp

    def addCheckbox(self,dispname, varname):
        print(dispname,varname)
        exec("self."+varname+"=QtWidgets.QCheckBox(self.groupBox)")
        exec("self.checkboxname=self."+varname)
        self.checkboxname.setObjectName(varname)
        self.checkboxname.setChecked(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.checkboxname.setFont(font)
        # self.checkbox3.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.checkboxname.setText(dispname)
        self.checkboxname.setChecked(True)
        # self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.checkbox3)
        self.formLayout.setWidget(self.checkboxcount, QtWidgets.QFormLayout.LabelRole, self.checkboxname)
        self.checkboxname.stateChanged['int'].connect(self.eventHandler)
        self.checkboxcount+=1
        return varname

    def autoTuneUI_update(self,disable:bool):
            self.groupBox_2.setDisabled(disable)
            self.autotuneSetpoint.setDisabled(disable)
            self.autotuneControlAmp.setDisabled(disable)
            self.autotuneControlFineAmp.setDisabled(disable)
            self.autotuneCycles.setDisabled(disable)
            self.Setpoint.setDisabled(disable)
            self.AutotuneMethod.setDisabled(disable)



    def variableProbe(self,name):
        return eval('self.'+name)



app=QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()