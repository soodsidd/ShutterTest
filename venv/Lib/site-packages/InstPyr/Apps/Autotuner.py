from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import *
from PyQt5 import QtCore
import sys
from src.InstPyr.UI import mainpanel_autotuner
from queue import Queue
import time
from src.InstPyr.Plotting import Plotter
from src.InstPyr.Control import PID
from gekko import GEKKO
from scipy.signal import tf2ss
import numpy as np

OVERSHOOT_WEIGHT=0

class MainWindow(QMainWindow,mainpanel_autotuner.Ui_MainWindow):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.setupUi(self)


        self.TF_num=[]
        self.TF_den=[]

        #Controlvariables
        self.Kcini=0
        self.KcLb=0
        self.KcUb=0
        self.Tiini=0
        self.TiLb=0
        self.TiUb=0
        self.Tdini=0
        self.TdLb=0
        self.TdUb =0
        self.outmin=0
        self.outmax=0




        #setup widgets
        self.mainplot=Plotter.MyPlotter(self.Plot1, initdata={'Setpoint':[],
                                                              'Process Variable':[]},buffersize=1000,oneaxis=True,datetimeaxis=False)

        self.controllerplot = Plotter.MyPlotter(self.Plot2, initdata={'ControlSignal': []}, buffersize=1000, oneaxis=True,
                                          datetimeaxis=False)

        # self.mainplot.updatedata([self.m.time,self.step])
        # self.mainplot.redraw()

    def eventHandler(self,*args):
        name=self.sender().objectName()
        print(name)

        if name=='Autotune':
            self.parseTF()
            self.parsePID()
            try:
                #TODO make separate thread for this
                pidv,res=PID.PID.autotune_offline(self.TF_num, self.TF_den, self.simDuration.value(), self.timeSteps.value(),
                                                  self.stepAmp.value(),
                                                  self.KcLb, self.KcUb,
                                                  self.TiLb, self.TiUb,
                                                  self.TdLb, self.TdUb,
                                                  self.outmin, self.outmax,
                                                  self.doubleSpinBox.value(),
                                                  self.riseweight.value(),
                                                  self.settlingweight.value())
                print('Kc: ' + str(pidv.Kc))
                print('Ti: ' + str(pidv.Ti))
                print('Td: ' + str(pidv.Td))
                self.Kc_ini.setValue(pidv.Kc)
                self.Ti_ini.setValue(pidv.Ti)
                self.Td_ini.setValue(pidv.Td)
                self.plotresponse(res.time, res.step, res.PV, res.OP)
            except Exception:
                pidv=0
                res=0

            # self.autotune()

        if name=='Simulate':
            pass

    def parseTF(self):
        self.TF_num=self.parseArray(self.Tfnum.text())
        self.TF_den= self.parseArray(self.Tfden.text())

    def parseArray(self,text):
        return [float(x) for x in text.strip('][').split(',')]

    def parsePID(self):
        self.Kcini=self.Kc_ini.value()
        self.KcLb=self.Kc_lb.value()
        self.KcUb=self.Kc_ub.value()
        self.Tiini=self.Ti_ini.value()
        self.TiLb=self.Ti_lb.value()
        self.TiUb=self.Ti_ub.value()
        self.Tdini=self.Td_ini.value()
        self.TdLb=self.Td_lb.value()
        self.TdUb=self.Td_ub.value()
        self.outmin=self.out_min.value()
        self.outmax=self.out_max.value()

    def plotresponse(self,time,step,PV,OP):
        self.mainplot.clear()
        self.controllerplot.clear()
        self.mainplot.updatedata([time,step,PV])
        self.controllerplot.updatedata([time,OP])
        self.mainplot.redraw()
        self.controllerplot.redraw()


if __name__=="__main__":
    app=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    app.exec_()