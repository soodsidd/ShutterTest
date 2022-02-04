from datetime import datetime
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time
import numpy as np
# from cycler import cycler
import numpy as np

class MyPlotter:
    def __init__(self, PlotWidget, buffersize=100, initdata=None, oneaxis=False, datetimeaxis=True):
        # setup the plot here- empty data
        #initdata must be a dictionary
        #initialize plotdata objects

        self.pltdata={}
        self.buffer = buffersize
        self.plotwidget = PlotWidget
        lines = 0
        self.ax2 = None
        self.oneaxis = oneaxis
        self.legend = True
        self.autoscale=True
        self.ylims=[0,0]
        self.datetimeaxis=datetimeaxis

        #connect plotwidget signals - these are signals from UI interactions with this widget
        self.plotwidget.auto_scale.connect(self._toolbaractive)
        self.plotwidget.xvariable_sig.connect(self._xchanged)
        self.plotwidget.yvarsLeft_sig.connect(self._yvarsLeft)
        self.plotwidget.yvarsRight_sig.connect(self._yvarsRight)
        self.plotwidget.zoomsig.connect(self._horZoomChanged)

        self.plotwidget.populateVariables(['P gain','Control signal','D gain','G gain','Error','Temperature','Pressure','Humidity'])

        self.plotwidget.canvas.ax.margins(x=0)


        #TODO combine plotdata initialization and plot initization using 'addLine' function
        if initdata is None:
            #make a default plotdata object
            self.pltdata['default']=_plotdata([],[],'default')
        elif isinstance(initdata, list):
            self.pltdata['default']=_plotdata(initdata[0], initdata[1], 'default')
        elif isinstance(initdata,dict):
            #determine number of lines
            if len(initdata)>2 and oneaxis is False:
                raise Exception('Too many arguments')
            for line in initdata.keys():
                if initdata[line]==[]:
                    self.pltdata[line] = _plotdata([], [], line,self.buffer)
                else:
                    self.pltdata[line]=_plotdata(initdata[line][0], initdata[line][1],line)
        else:
            raise Exception('Improper arguments')

        #hold xdata and ydata in a dictionary

        for pltdta in self.pltdata.values():
            lines+=1
            if not lines>=2:
                if self.datetimeaxis:
                    plot_refs = self.plotwidget.canvas.ax.plot_date(pltdta.xdata, pltdta.ydata, label=pltdta.name,fmt='-b')
                else:
                    plot_refs=self.plotwidget.canvas.ax.plot(pltdta.xdata,pltdta.ydata,label=pltdta.name)
                pltdta._plot_ref = plot_refs[0]
                if not oneaxis:
                    #if oneaxis is true, then have a legend
                    #also set here the ability to annotate current value

                    self.plotwidget.canvas.ax.set_ylabel(pltdta.name)
                    self.plotwidget.canvas.ax.yaxis.label.set_color('blue')
                    self.plotwidget.canvas.ax.tick_params(axis='y', colors='blue')
            elif oneaxis:
                if self.datetimeaxis:
                    plot_refs = self.plotwidget.canvas.ax.plot_date(pltdta.xdata, pltdta.ydata, label=pltdta.name, fmt='-')
                else:
                    plot_refs=self.plotwidget.canvas.ax.plot(pltdta.xdata,pltdta.ydata,label=pltdta.name)
                self.legend=True
                pltdta._plot_ref = plot_refs[0]

            else:
                self.ax2=self.plotwidget.canvas.ax.twinx()
                if self.datetimeaxis:
                    plot_refs=self.ax2.plot_date(pltdta.xdata,pltdta.ydata,label=pltdta.name,fmt='-r')
                else:
                    plot_refs=self.ax2.plot(pltdta.xdata,pltdta.ydata,label=pltdta.name)
                self.ax2.set_ylabel(pltdta.name)
                self.ax2.yaxis.label.set_color('red')
                self.ax2.tick_params(axis='y', colors='red')
                pltdta._plot_ref=plot_refs[0]

    def _toolbaractive(self,active):
        # print('Triggered'+str(active))
        self.autoscale=True if active==0 else False
        # print(self.autoscale)

    def _xchanged(self,params):
        print(params)

    def _yvarsLeft(self,params):
        print(params)

    def _yvarsRight(self,params):
        print(params)

    def _horZoomChanged(self,params):
        print(params)

    @property
    def legend(self):
        return self._legend
    @legend.setter
    def legend(self,val):
        self._legend=val
        if val==False:
            if self.plotwidget.canvas.ax.get_legend() is not None:
                self.plotwidget.canvas.ax.get_legend().remove()
        else:
            self.plotwidget.canvas.ax.legend(loc=3)

    @property
    def buffer(self):
        return self._buffer

    @buffer.setter
    def buffer(self,val):
        self._buffer=val
        for key in self.pltdata.keys():
            self.pltdata[key].buffersize=val


    def changeAxes(self,data,plotparameters=None):
        #call this function if you change axes after initialization
        #data can be a dictionary
        pass

    def removeLine(self,linename):
        if linename in list(self.pltdata.keys()):
            del self.pltdata[linename]
            for line in self.plotwidget.canvas.ax.lines:
                if line.get_label()==linename:
                    self.plotwidget.canvas.ax.lines.remove(line)

    def addLine(self,linename,data=None, linefmt=None):
        #TODO have ability to add a new line such that it is on the twin axis
        if linefmt==None:
            if self.datetimeaxis:
                plot_refs = self.plotwidget.canvas.ax.plot_date([], [], label=linename,
                                                        fmt='-',drawstyle='default')
            else:
                plot_refs=self.plotwidget.canvas.ax.plot([],[],label=linename,
                                                         fmt='-',drawstyle='default')
        else:
            if self.datetimeaxis:
                plot_refs = self.plotwidget.canvas.ax.plot_date([], [], label=linename,
                                                            fmt=linefmt,drawstyle='default')
            else:
                plot_refs = self.plotwidget.canvas.ax.plot([], [], label=linename,
                                                            fmt=linefmt,drawstyle='default')
        self.legend = True
        self.pltdata[linename] = _plotdata([], [], linename,self.buffer)
        self.pltdata[linename]._plot_ref = plot_refs[0]
        if data is not None:
            self.pltdata[linename].update(data[0], data[1])
        self.oneaxis = True

    def updatedata(self,data):
        #data is a dictionary or a simple list
        #if there are two lines initialized and only one data is supplied, the data goes to the first plotdata object
        firstkey=list(self.pltdata.keys())[0]
        start=0
        if isinstance(data, list):
            #data here is going to be 'timestamp' followed by data
            if any(isinstance(el, list) for el in data) or any(isinstance(el, np.ndarray) for el in data):
                # if len(data[0]) is not len(data[1]):
                #     print(len(data[0]))
                #     print(len(data[1]))
                #     print('Bad data')
                # else:
                for i in range(len(data[0])):
                    start=0
                    for key in self.pltdata.keys():
                        try:
                            self.pltdata[key].update(data[0][i],data[start+1][i])
                            start+=1
                        except Exception:
                            print('no data here')
                            break
            else:
                for key in self.pltdata.keys():
                    self.pltdata[key].update(data[0],data[start+1])
                    start+=1
                # self.pltdata[firstkey].update(data[0],data[1])
        elif isinstance(data,dict):
            #TODO add ability to accept dictionary of complete datasets
            #this dictionary could have 1 or 2 data objects
            for key in list(data.keys()):
                if key in list(self.pltdata.keys()):
                    self.pltdata[key].update(data[key][0],data[key][1])
                else:
                    #create a line for the new axis
                    if self.datetimeaxis:
                        plot_refs = self.plotwidget.canvas.ax.plot_date([], [], label=key,
                                                                    fmt='-',drawstyle='default')
                    else:
                        plot_refs = self.plotwidget.canvas.ax.plot([], [], label=key,
                                                                        fmt='-', drawstyle='default')
                    self.legend = True
                    self.pltdata[key]=_plotdata([],[],key,self.buffer)
                    self.pltdata[key]._plot_ref= plot_refs[0]
                    self.pltdata[key].update(data[key][0],data[key][1])
                    self.oneaxis=True
        else:
            raise Exception('bad data')
    def hide(self,linename):
        if linename in list(self.pltdata.keys()):
            self.pltdata[linename].visible=False

    def show(self,linename):
        if linename in list(self.pltdata.keys()):
            self.pltdata[linename].visible=True

    def clear(self,key=None):
        if key==None:
            for key in list(self.pltdata.keys()):
                self.pltdata[key].xdata=[]
                self.pltdata[key].ydata=[]
                self.pltdata[key].plotlen=0
        else:
            if key in list(self.pltdata.keys()):
                self.pltdata[key].xdata = []
                self.pltdata[key].ydata = []
                self.pltdata[key].plotlen=0

    def redraw(self):
        # update plot here
        if self.autoscale:
            self.plotwidget.canvas.ax.relim()
            self.plotwidget.canvas.ax.autoscale()


            if self.oneaxis and self.legend:
                self.legend=True
            if self.ax2 is not None:
                self.ax2.relim()
                self.ax2.autoscale()
            # firstkey=list(self.pltdata.keys())[0]
            # if self.pltdata[firstkey].plotlen >= self.buffer:
            #     x_lims=[self.pltdata[firstkey].xdata[self.pltdata[firstkey].plotlen - self.buffer],self.pltdata[firstkey].xdata[self.pltdata[firstkey].plotlen - 1]]
            #     self.plotwidget.canvas.ax.set_xlim(left=x_lims[0],
            #                                    right=x_lims[1])
            #
            #     self.plotwidget.canvas.ax.autoscale(axis='y')

        self.plotwidget.canvas.draw_idle()

    def annotate(self,msg,timestamp=None):
        firstkey = list(self.pltdata.keys())[0]
        pltlen=len(self.pltdata[firstkey].xdata)
        if timestamp==None:
            #annotate at latest timestamp
            self.plotwidget.canvas.ax.annotate(msg,(self.pltdata[firstkey].xdata[pltlen-1],self.pltdata[firstkey].ydata[pltlen-1]))




class _plotdata:
    #use this class to format data for plots- especially where multiple lines are needed
    def __init__(self,xdata,ydata,name,buffersize):
        self.buffersize=buffersize
        if not isinstance(xdata,list):
            self.xdata=[xdata]
            self.ydata=[ydata]
        else:
            self.xdata=xdata
            self.ydata=ydata
        self.name=name
        self.plotlen=len(self.xdata)
        self._plot_ref=None
        self.visible=True

    def update(self,xdata,ydata):
        self.xdata.append(xdata)
        self.ydata.append(ydata)
        self.plotlen+=1
        if self.plotlen>=self.buffersize:
            lowind=self.plotlen-self.buffersize
            highind=self.plotlen-1
        else:
            lowind=0
            highind=self.plotlen-1
        if self.visible:
            self._plot_ref.set_data(self.xdata[lowind:highind],self.ydata[lowind:highind])
            self._plot_ref.set_label(self.name+':'+f"{ydata:.2f}")
        else:
            self._plot_ref.set_data(None,None)
            self._plot_ref.set_label('_nolegend_')


class _PlotTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.w=MplWidget()
        # self.myplot=MyPlotter(self.w,initdata={'A':[datetime.now(),0],'B':[datetime.now(),0]})
        # self.myplot=MyPlotter(self.w,initdata={'Temperature_innercore':[],
        #                                        'Temperature_skirt':[],
        #                                        'Temperature_lid':[]}, oneaxis=True)
        self.myplot=MyPlotter(self.w,initdata={'Temperature_innercore':[],
                                               'Temperature_lid':[]}, buffersize=100000, oneaxis=True,datetimeaxis=False)
        # self.myplot.removeLine('Temperature_skirt')
        # self.myplot.addLine('Temperature_Ambient')
        # self.myplot2=MyPlotter(self.w,100)
        # self.myplot3=MyPlotter(self.w, 100)
        self.setCentralWidget(self.w)
        self.timer=QtCore.QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.updateTestPlot)
        self.timer.start()


    def updateTestPlot(self):

        # self.myplot.updatedata({'A':[datetime.now(),np.random.randint(5)],'B':[datetime.now(),np.random.randint(7)]})#,[datetime.now(),2*np.random.randint(5)]])
        # self.myplot.updatedata({'Temperature_innercore':[datetime.now(),105.23-np.random.randint(5)]})
        # # self.myplot.updatedata({'Temperature_skirt': [datetime.now(), 80.12 - np.random.randint(5)]})
        # self.myplot.updatedata({'Temperature_lid': [datetime.now(), 30.12 - np.random.randint(5)]})
        d1=105.23-np.random.randint(5)
        d2=80.12-np.random.randint(5)
        self.myplot.updatedata([datetime.now(),d1,d2])
        self.myplot.hide('Temperature_lid')
        if d1>105:
            self.myplot.annotate('Hi')
            self.myplot.show('Temperature_lid')

        # self.myplot.legend=False
        # self.myplot.autoscale=True

        self.myplot.redraw()
        # self.myplot2.redraw()


if __name__=="__main__":
    from mplwidget import MplWidget

    app = QApplication(sys.argv)
    window=_PlotTester()
    window.show()
    app.exec_()


