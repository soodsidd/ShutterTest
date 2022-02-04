from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import *
from PyQt5 import QtCore
import sys
from src.InstPyr.UI import mainpanel_sysid
from queue import Queue
import time
from src.InstPyr.Plotting import Plotter
from src.InstPyr.Control import SysId
from gekko import GEKKO
from scipy.signal import tf2ss
import numpy as np
import pandas as pd
from ast import literal_eval
import xlrd


class MainWindow(QMainWindow,mainpanel_sysid.Ui_MainWindow):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.setupUi(self)

        self.df=0
        self.fname=0
        self.time=[]
        self.input=[]
        self.actual=[]
        self.model=[]
        self.modelselected=0

        self.sysID=SysId.TF_identificator()
        self.showParameters(0)




        #setup widgets
        self.mainplot=Plotter.MyPlotter(self.plot, initdata={'Input':[],
                                                              'Actual':[],
                                                             'Model':[]},buffersize=100000,oneaxis=True,datetimeaxis=False)



        # self.mainplot.updatedata([self.m.time,self.step])
        # self.mainplot.redraw()

    def eventHandler(self,*args):
        name=self.sender().objectName()
        print(name)

        if name=='loadModel':
            self.fname=self.filename.toPlainText()
            print(self.fname)
            self.df=pd.read_excel(self.fname)
            print(self.df)
            self.time=self.df['Time'].to_list()
            self.input=self.df['Input'].to_list()
            self.actual=self.df['Output'].to_list()

            self.mainplot.clear()
            self.mainplot.updatedata([self.time,self.input,self.actual])
            self.mainplot.redraw()

        if name=='modelselect':
            if self.modelselect.currentIndex()==0:
                self.modelselected=0
                self.showParameters(0)
            else:
                self.modelselected=1
                self.showParameters(1)
        if name=='CuveFit':
            if self.modelselect.currentIndex()==0:
                #first order model
                self.showParameters(0)
                params=self.sysID.identify_first_order_gek(self.time, self.input,self.actual)
                k=params['k']
                tau=params['tau']
                self.K_fo.setText(str(params['k']))
                self.k_fo_max.setValue(1.5*k)
                self.k_fo_min.setValue(0.5*k)
                self.Tau_fo.setText(str(params['tau']))
                self.tau_fo_max.setValue(1.5*tau)
                self.tau_fo_min.setValue(0.5*tau)
                self.Tf_num.setText('['+str(k)+']')
                self.Tf_den.setText('['+str(tau)+',1]')
                simout=params['sim']
                res=params['res']
                self.label_4.setText(str(res))
                self.mainplot.clear('Model')
                for i in range(len(simout)):
                    self.mainplot.updatedata({'Model':[self.time[i],simout[i]]})
                self.mainplot.redraw()
            else:
                self.showParameters(1)
                params = self.sysID.identify_second_order_damped(self.time, self.input, self.actual, dynamicsratiomax=self.spinBox.value())
                k = params['k']
                T1 = params['T1']
                T2=params['T2']
                T3 = params['T3']
                self.K_so.setText(str(k))
                self.k_so_max.setValue(1.5*k)
                self.k_so_min.setValue(0.5 * k)

                self.T1_so.setText(str(T1))
                self.T1_so_max.setValue(1.5*T1)
                self.T1_so_min.setValue(0.5*T1)
                self.T2_so.setText(str(T2))
                self.T2_so_max.setValue(1.5*T2)
                self.T2_so_min.setValue(0.5*T2)
                self.T3_so.setText(str(T3))
                self.T3_so_max.setValue(1.5*T3)
                self.T3_so_min.setValue(0.5*T3)

                self.Tf_num.setText('[{:.1f},{:.1f}]'.format(k*T3,k))
                self.Tf_den.setText('[{:.1f},{:.1f},1]'.format(T1*T2,(T1+T2)))
                res=params['res']
                simout = params['sim']
                self.label_4.setText(str(res))
                self.mainplot.clear('Model')
                for i in range(len(simout)):
                    self.mainplot.updatedata({'Model': [self.time[i], simout[i]]})
                self.mainplot.redraw()

        #TODO REFACTOR
        if name=='k_fo_slider':
            kmax=self.k_fo_max.value()
            kmin=self.k_fo_min.value()
            slider=self.k_fo_slider.value()
            knew=kmin+(kmax-kmin)*slider/100
            tau=float(self.Tau_fo.text())
            self.K_fo.setText(str(knew))
            try:
                simout=self.sysID.first_order_mdl(self.time,self.input,knew,tau)
                self.updateModelPlot(simout)
            except Exception:
                print('Bad inputs')

        if name=='tau_fo_slider':
            taumax=self.tau_fo_max.value()
            taumin=self.tau_fo_min.value()
            slider=self.tau_fo_slider.value()
            taunew=taumin+(taumax-taumin)*slider/100
            k=float(self.K_fo.text())
            self.Tau_fo.setText(str(taunew))
            try:
                simout=self.sysID.first_order_mdl(self.time,self.input,k,taunew)
                self.updateModelPlot(simout)
            except Exception:
                print('Bad inputs')

        if name=='k_so_slider':
            kmax=self.k_so_max.value()
            kmin=self.k_so_min.value()
            slider=self.k_so_slider.value()
            knew=kmin+(kmax-kmin)*slider/100
            T1=float(self.T1_so.text())
            T2 = float(self.T2_so.text())
            T3 = float(self.T3_so.text())
            self.K_so.setText(str(knew))
            try:
                simout=self.sysID.second_order_mdl_overdamped(self.time, self.input,knew,T1,T2,T3)
                self.updateModelPlot(simout)
            except Exception:
                print('Bad inputs')

        if name=='T1_so_slider':
            T1max=self.T1_so_max.value()
            T1min=self.T1_so_min.value()
            slider=self.T1_so_slider.value()
            T1new=T1min+(T1max-T1min)*slider/100
            k=float(self.K_so.text())
            T2 = float(self.T2_so.text())
            T3 = float(self.T3_so.text())
            self.T1_so.setText(str(T1new))
            try:
                simout=self.sysID.second_order_mdl_overdamped(self.time, self.input,k,T1new,T2,T3)
                self.updateModelPlot(simout)
            except Exception:
                print('Bad inputs')

        if name=='T2_so_slider':
            T2max=self.T2_so_max.value()
            T2min=self.T2_so_min.value()
            slider=self.T2_so_slider.value()
            T2new=T2min+(T2max-T2min)*slider/100
            k=float(self.K_so.text())
            T1 = float(self.T1_so.text())
            T3 = float(self.T3_so.text())
            self.T2_so.setText(str(T2new))
            try:
                simout=self.sysID.second_order_mdl_overdamped(self.time, self.input,k,T1,T2new,T3)
                self.updateModelPlot(simout)
            except Exception:
                print('Bad inputs')

        if name=='T3_so_slider':
            T3max=self.T3_so_max.value()
            T3min=self.T3_so_min.value()
            slider=self.T3_so_slider.value()
            T3new=T3min+(T3max-T3min)*slider/100
            k=float(self.K_so.text())
            T2 = float(self.T2_so.text())
            T1 = float(self.T1_so.text())
            self.T3_so.setText(str(T3new))
            try:
                simout=self.sysID.second_order_mdl_overdamped(self.time, self.input,k,T1,T2,T3new)
                self.updateModelPlot(simout)
            except Exception:
                print('Bad inputs')


    def showParameters(self,order):
        if order==0:
            self.firstOrderModel.setVisible(True)
            self.secondOrderModel.setVisible(False)
            self.secondOrderParams.setVisible(False)
        else:
            self.firstOrderModel.setVisible(False)
            self.secondOrderModel.setVisible(True)
            self.secondOrderParams.setVisible(True)

    def updateModelPlot(self,simout):
        self.mainplot.clear('Model')
        for i in range(len(simout)):
            self.mainplot.updatedata({'Model': [self.time[i], simout[i]]})
        self.mainplot.redraw()
        res = self.sysID.calculate_residual(self.actual, simout)
        self.label_4.setText(str(res))






if __name__=="__main__":
    app=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    app.exec_()