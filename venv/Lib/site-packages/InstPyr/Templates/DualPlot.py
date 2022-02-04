from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import *
from PyQt5 import QtCore
import sys
from queue import Queue
from datetime import datetime
import os
import numpy as np
path=os.getcwd()
curr=os.path.basename(path)
if curr=='Templates':
    from src.InstPyr.UI import DualPlotUI
    import src.InstPyr.Interfaces.simulator as simulator
    from src.InstPyr.Plotting.PlotterWatch import MyPlotterWatch as Plotter
    from src.InstPyr.Logging import Logger
    from src.InstPyr.Utilities.watch import watch
    from src.InstPyr.Control.Filter import MyFilter
else:
    from InstPyr.UI import DualPlotUI
    import InstPyr.Interfaces.simulator as simulator
    from InstPyr.Plotting.PlotterWatch import MyPlotterWatch as Plotter
    from InstPyr.Logging import Logger
    from InstPyr.Utilities.watch import watch


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

class MainWindow(QMainWindow,DualPlotUI.Ui_MainWindow):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.setupUi(self)
        self.ControlBay.hide()
        #Setup variables
        self.watchlist=[]
        self.logger = None
        self.samplingrate = int(1000/self.Sampling.value())
        self.logfilename = ''
        self.logenable = False


        #************YOUR CODE GOES HERE************

        #setup interface and devices
        self.interface=simulator.simulator()

        #setup variables
        self.realTemp = 0
        self.procTemp=0
        self.lidTemp=0
        self.realTemp_filtered=0
        self.scalefactor=1
        self.targetinst=''


        #Define Controls,Define callback functions past 'MainLoop'
        self.addNumeric('Setpoint',self.setpointchange,-1,1,0.1)
        self.addButton('Push Me',self.buttonpush,latching=True)
        subcon=self.addGroup('Sub Controls')
        self.addNumeric('Average Points',self.filterchange,1,1000,1,50,parent=subcon)
        self.addDropdown('Instrument List',['2001dn','2002dn'],self.dropdownchanged,parent=subcon)
        self.addButton('Connect',self.instconnect, parent=subcon)



        #setup a 'watch' for every variable that you want to plot
        self.watchlist.append(watch('Real Temperature (C)',nameof(self.realTemp),callfunc=self.variableProbe))
        self.watchlist.append(watch('Real Temp(filt) (C)', nameof(self.realTemp_filtered),callfunc=self.variableProbe))
        self.watchlist.append(watch('Process Temperature (C)', nameof(self.procTemp),callfunc=self.variableProbe))
        self.watchlist.append(watch('Lid Temperature (C)', nameof(self.lidTemp),callfunc=self.variableProbe))



        #************STATIC CODE************
        #setup widgets
        self.plot_top=Plotter(self.Mainplot_top,variables=self.watchlist)
        self.plot_bottom=Plotter(self.Mainplot_bottom,variables=self.watchlist)
        #setup threads
        self.threadpool=QThreadPool()
        self.dispQueue=Queue()
        dispWorker=Worker(self.update_display)
        self.threadpool.start(dispWorker)

        self.logQueue = Queue()
        logWorker = Worker(self.logdata)
        self.threadpool.start(logWorker)

        self.eventQueue=Queue()

        #Define mainloop timer
        self.timer=QtCore.QTimer()
        self.timer.setInterval(self.samplingrate)
        self.timer.timeout.connect(self.mainloop)
        self.timer.start()
        self.logQueue.join()
        self.dispQueue.join()

        #Redefine UI
        if len(self.ControlBay.findChildren(QtWidgets.QWidget)) is not 0:
            self.ControlBay.show()

        #Reformat watchlist:
        temp={}
        for item in self.watchlist:
            name=item.variableName
            temp[name]=item
        self.watchlist=temp




    def mainloop(self):
        #************YOUR CODE GOES HERE************
        self.realTemp=self.scalefactor*self.interface.readTemperature(0)
        self.procTemp=self.interface.readTemperature(0)/1000000
        self.lidTemp=self.interface.readTemperature(0)
        self.realTemp_filtered=np.mean(list(self.watchlist['realTemp'].buffer))




        #************STATIC CODE************
        self.loadqueues()

    # ************YOUR CODE GOES HERE************
    #Define callback functions for custom controls here
    def buttonpush(self,val):
        print('here'+str(val))

    def setpointchange(self,val):
        print('here'+str(val))
        self.scalefactor=val

    def filterchange(self,val):
        print('here' + str(val))
        self.watchlist[0].buffersize=val

    def instconnect(self,val):
        print(val)

    def dropdownchanged(self,val):
        print(val)




    # ************STATIC CODE************
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
            self.plot_top.updatedata(time,vardata)
            self.plot_bottom.updatedata(time,vardata)
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
    def addButton(self,name,callback,latching=False,parent=None):
        btn=QtWidgets.QPushButton(name)
        font = QtGui.QFont()
        font.setPointSize(8)
        btn.setFont(font)
        btn.setCheckable(latching)
        btn.clicked['bool'].connect(callback)
        if parent is None:
            self.verticalLayout_6.addWidget(btn)
        else:
            parent.addWidget(btn)
    def addNumeric(self,label,callback,min=0,max=100,stepsize=1.0,default=0,parent=None):
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
        doubleEdit.valueChanged['double'].connect(callback)

        pass
    def addGroup(self,name,parent=None):
        gbox=QtWidgets.QGroupBox(name)
        glayout=QtWidgets.QVBoxLayout(gbox)
        font = QtGui.QFont()
        font.setPointSize(10)
        gbox.setFont(font)
        self.verticalLayout_6.addWidget(gbox)
        return glayout
    def addDropdown(self, label,items,callback,parent=None):
        vbox=QtWidgets.QVBoxLayout()
        label=QtWidgets.QLabel(label)
        font = QtGui.QFont()
        font.setPointSize(8)
        label.setFont(font)

        drpdown=QtWidgets.QComboBox()
        drpdown.setFont(font)
        drpdown.addItems(items)
        drpdown.setCurrentIndex(0)

        drpdown.currentIndexChanged['QString'].connect(callback)

        vbox.addWidget(label)
        vbox.addWidget(drpdown)

        if parent==None:
            self.verticalLayout_6.addLayout(vbox)
        else:
            parent.addLayout(vbox)

app=QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()