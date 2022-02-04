import threading

from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import *
from PyQt5 import QtCore
import sys
import time
from queue import Queue
from datetime import datetime
import os
import numpy as np
path=os.getcwd()
curr=os.path.basename(path)
if curr=='Templates':
    from src.InstPyr.UI import SinglePlotUI
    import src.InstPyr.Interfaces.simulator as simulator
    from src.InstPyr.Plotting.PlotterWatch import MyPlotterWatch as Plotter
    from src.InstPyr.Logging import Logger
    from src.InstPyr.Utilities.watch import watch
    from src.InstPyr.Control.Plant import Plant
    from src.InstPyr.Control.Filter import MyFilter,RateLimiter
    from src.InstPyr.Control.Waveform import *
    from src.InstPyr.Utilities.shiftregister import shiftregister
else:
    from InstPyr.UI import SinglePlotUI
    import InstPyr.Interfaces.simulator as simulator
    from InstPyr.Plotting.PlotterWatch import MyPlotterWatch as Plotter
    from InstPyr.Logging import Logger
    from InstPyr.Control.Plant import Plant
    from InstPyr.Utilities.watch import watch
    from InstPyr.Utilities.shiftregister import shiftregister
    from InstPyr.Control.Filter import MyFilter,RateLimiter
    from InstPyr.Control.Waveform import *


from varname import nameof
#************STATIC CODE************
class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)

class MainWindow(QMainWindow,SinglePlotUI.Ui_MainWindow):
    def __init__(self):
        #************STATIC CODE************
        super(self.__class__,self).__init__()
        self._appsetup()


        #************YOUR CODE GOES HERE************
        #setup interface and devices
        self.interface=simulator.simulator()
        self.simsystem=Plant([1],[1,0.5,1])

        #setup variables
        self.realTemp = 0
        self.procTemp=0
        self.lidTemp=0
        self.processoutput=0
        self.realTemp_filtered=0
        self.scalefactor=1
        self.targetinst=''
        self.realTempRegister=shiftregister(size=10)
        self.rampfilter=RateLimiter(1)


        #Define Controls,Define callback functions past 'MainLoop'
        self.addNumeric('Setpoint',-1,1,0.1,callback=lambda val: setattr(self,'scalefactor',val))
        self.pushbtn=self.addButton('Push Me',latching=True,callback=lambda val: self.startThread(self.asychronousMethod) if val is True else print('this')) #can manipulate pushbtn later if necessary
        subcon=self.addGroup('Sub Controls')
        self.addNumeric('RampRate (C/sec)',1,1000,1,1,parent=subcon,callback= lambda val: setattr(self.rampfilter,'maxrate',val))
        self.addDropdown('Instrument List',['2001dn','2002dn'],parent=subcon,callback=self.dropdownchanged)
        self.addButton('Connect', parent=subcon,callback=self.instconnect)


        #setup a 'watch' for every variable that you want to plot
        self.watchlist.append(watch('Real Temperature (C)',nameof(self.realTemp),callfunc=self.variableProbe))
        self.watchlist.append(watch('Real Temp(filt) (C)', nameof(self.realTemp_filtered),callfunc=self.variableProbe))
        self.watchlist.append(watch('Process Output', nameof(self.processoutput),callfunc=self.variableProbe))
        self.watchlist.append(watch('Process Temperature (C)', nameof(self.procTemp),callfunc=self.variableProbe))
        self.watchlist.append(watch('Lid Temperature (C)', nameof(self.lidTemp),callfunc=self.variableProbe))


        #************STATIC CODE************
        self._postInit()


    def mainloop(self):
        #************YOUR CODE GOES HERE************
        #use this for accurate timekeeping
        newtime=time.time()
        elapsedtime=newtime-self.currentTime
        self.currentTime=newtime

        #update statusbar here:
        self.setStatus('Online')

        self.realTemp=self.scalefactor*self.interface.readTemperature(0)
        self.realTempRegister.push(self.realTemp)
        self.procTemp=self.interface.readTemperature(0)/1000000
        self.lidTemp=self.interface.readTemperature(0)
        self.realTemp_filtered=self.rampfilter.nextVal(self.realTemp)
        self.processoutput=self.simsystem.realTime(self.realTemp,self.currentTime)


        #************STATIC CODE************
        self.loadqueues()


    # ************YOUR CODE GOES HERE************
    #use this method for asynchronous function calls (that could use a separate thread)
    def asychronousMethod(self):
        for i in range(50):
            time.sleep(1)
            print(i)
        self.pushbtn.setChecked(False)



    #Define callbacks functions for your controls here
    def instconnect(self,val):
        print(val)

    def dropdownchanged(self,val):
        print(val)




    # ************STATIC CODE************
    def _appsetup(self):
        self.setupUi(self)
        self.ControlBay.hide()
        #Setup variables
        self.watchlist=[]
        self.logger = None
        self.samplingrate = int(1000/self.Sampling.value())
        self.logfilename = ''
        self.logenable = False
        self.currentTime=time.time()
    def _postInit(self):
        # ************STATIC CODE************
        # setup widgets
        self.plot = Plotter(self.Mainplot,datetimeaxis=False, variables=self.watchlist)
        # setup threads
        self.lock=threading.Lock
        self.threadpool = QThreadPool()
        self.dispQueue = Queue()
        dispWorker = Worker(self.update_display)
        self.threadpool.start(dispWorker)

        self.logQueue = Queue()
        logWorker = Worker(self.logdata)
        self.threadpool.start(logWorker)

        self.eventQueue = Queue()

        # Define mainloop timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.samplingrate)
        self.timer.timeout.connect(self.mainloop)
        self.timer.start()
        self.logQueue.join()
        self.dispQueue.join()

        # Redefine UI
        if len(self.ControlBay.findChildren(QtWidgets.QWidget)) is not 0:
            self.ControlBay.show()

        # Reformat watchlist:
        temp = {}
        for item in self.watchlist:
            name = item.variableName
            temp[name] = item
        self.watchlist = temp
    def loadqueues(self):
        vardata = {}
        for watch in self.watchlist.values():
            vardata[watch.name] = watch.read()
        data = [datetime.now(), vardata]
        self.dispQueue.put(data)
        if self.logenable:
            try:
                event = self.eventQueue.get(timeout=0.1)
                self.logQueue.put(data + [event])
            except Exception:
                self.logQueue.put(data)
    def update_display(self):
        while(True):
            data=self.dispQueue.get(timeout=1000)
            self.dispQueue.task_done()
            time=data[0]
            vardata=data[1]
            self.plot.updatedata(time,vardata)
    def logdata(self):
        while True:
            data = self.logQueue.get()
            self.logQueue.task_done()
            if self.logger is not None and self.logenable:
                writedata=[data[0]]
                for key in data[1].keys():
                    writedata.append(data[1][key])
                self.logger.writetimedata(writedata)
    def eventHandler(self,*args):
        name=self.sender().objectName()
        print(name)
        if name=="LogEnable":
            self.logenable=self.LogEnable.isChecked()
            if self.logenable is True and self.filename.toPlainText() != '':
                if self.logger is not None:
                    #if filename is new, create new logger
                    if self.logger.fname != self.filename.toPlainText():
                        #close previous file
                        self.logger.close()
                        try:
                            self.logger=Logger.Logger(self.filename.toPlainText(),[x.name for x in self.watchlist.values()],'w+')
                        except Exception as e:
                            print(e)
                            self.logger=None
                            self.LogEnable.setChecked(False)

                    else:
                        while not self.logQueue.empty():
                            try:
                                self.logQueue.get(False)
                            except Exception as e:
                                print(e)
                                continue
                            self.logQueue.task_done()
                        self.logger = Logger.Logger(self.filename.toPlainText(),
                                                    [x.name for x in self.watchlist.values()], 'a')
                else:
                    try:
                        self.logger = Logger.Logger(self.filename.toPlainText(), [x.name for x in self.watchlist.values()],'w+')
                    except Exception as e:
                        print(e)
                        self.logger=None
                        self.LogEnable.setChecked(False)
            elif self.logenable is False:
                if self.logger is not None:
                    self.logger.close()
        if name=='Buffersize':
            self.plot.buffer=int(self.Buffersize.value()*self.Sampling.value())
            self.statusmsg.emit('Changed show last')
        if name=='Sampling':
            # self.timer.stop()
            self.timer.setInterval(int(1000/self.Sampling.value()))
            self.samplingrate=self.Sampling.value()
        if name=='clear':
            self.plot.clear()
        if name=='annotate':
            self.plot.annotate(self.annotatemsg.toPlainText())
            if self.logEnable:
                #construct blank data:
                self.eventQueue.put(self.annotatemsg.toPlainText())
            self.annotatemsg.setText('')
    def variableProbe(self,name):
        return eval('self.'+name)
    def addButton(self,name,latching=False,parent=None,callback=None):
        btn=QtWidgets.QPushButton(name)
        font = QtGui.QFont()
        font.setPointSize(8)
        btn.setFont(font)
        btn.setCheckable(latching)
        if callback is not None:
            btn.clicked['bool'].connect(callback)
        if parent is None:
            self.verticalLayout_6.addWidget(btn)
        else:
            parent.addWidget(btn)
        return btn
    def addNumeric(self,label,min=0,max=100,stepsize=1.0,default=0,parent=None,callback=None):
        font = QtGui.QFont()
        font.setPointSize(8)
        label=QtWidgets.QLabel(label)
        label.setFont(font)
        doubleEdit=QtWidgets.QDoubleSpinBox()
        doubleEdit.setMinimum(min)
        doubleEdit.setMaximum(max)
        doubleEdit.setSingleStep(0.1)
        doubleEdit.setValue(default)
        doubleEdit.setFont(font)
        hbox=QtWidgets.QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(doubleEdit)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        doubleEdit.setSizePolicy(sizePolicy)
        if parent is None:
            self.verticalLayout_6.addLayout(hbox)
        else:
            parent.addLayout(hbox)
        doubleEdit.setKeyboardTracking(False)
        if callback is not None:
            doubleEdit.valueChanged['double'].connect(callback)
        return doubleEdit
    def addGroup(self,name,parent=None):
        gbox=QtWidgets.QGroupBox(name)
        glayout=QtWidgets.QVBoxLayout(gbox)
        font = QtGui.QFont()
        font.setPointSize(10)
        gbox.setFont(font)
        self.verticalLayout_6.addWidget(gbox)
        return glayout
    def addDropdown(self, label,items,parent=None,callback=None):
        vbox=QtWidgets.QVBoxLayout()
        label=QtWidgets.QLabel(label)
        font = QtGui.QFont()
        font.setPointSize(8)
        label.setFont(font)

        drpdown=QtWidgets.QComboBox()
        drpdown.setFont(font)
        drpdown.addItems(items)
        drpdown.setCurrentIndex(0)
        if callback is not None:
            drpdown.currentIndexChanged['QString'].connect(callback)

        vbox.addWidget(label)
        vbox.addWidget(drpdown)

        if parent==None:
            self.verticalLayout_6.addLayout(vbox)
        else:
            parent.addLayout(vbox)

        return drpdown
    def setStatus(self,text):
        self.Status.setText(text)
    def startThread(self,callback):
        wrkr = Worker(callback)
        self.threadpool.start(wrkr)

app=QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()