# Imports
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import pyqtSignal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib as mpl

# Ensure using PyQt5 backend
mpl.use('QT5Agg')

# Matplotlib canvas class to create figure
class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.minorticks_on()
        self.ax.grid(b=True, which='major', color='silver', linestyle='-')
        self.ax.grid(b=True, which='minor', color='gainsboro', linestyle='--')
        self.fig.tight_layout()
        self.fig.set_tight_layout(True)
        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.fig.canvas.mpl_connect('button_press_event',lambda event: self.btnpress(event))
        Canvas.updateGeometry(self)
# Matplotlib widget
class MplWidget(QtWidgets.QWidget):
    auto_scale=pyqtSignal(int,name='auto_scale')
    xvariable_sig=pyqtSignal(list,name='xvariable')
    yvarsLeft_sig=pyqtSignal(list,name='yvarsleft')
    yvarsRight_sig=pyqtSignal(list,name='yvarsRight')
    zoomsig=pyqtSignal(int,name='ZoomSignal')
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = MplCanvas()
        self.yvarsL=[]
        self.yvarsR=[]

        #Add widgets here:
        self.toolbar=myNavToolbar(self.canvas,self)
        self.showVars=QtWidgets.QRadioButton()
        self.Xlabel=QtWidgets.QLabel('X-Axis:')
        self.Ylabel=QtWidgets.QLabel(' Y-Axis:')
        self.Xchoices=QtWidgets.QComboBox()
        self.xaxisdropdown = QtWidgets.QHBoxLayout()
        self.xaxisdropdown.addStretch(1)
        self.xaxisdropdown.addWidget(self.Xlabel)
        self.xaxisdropdown.addWidget(self.Xchoices)
        self.xaxisdropdown.addStretch(1)
        self.variableselector=QtWidgets.QScrollArea()
        self.variableselectorlayout=QtWidgets.QVBoxLayout()
        self.variableselector.setLayout(self.variableselectorlayout)
        self.timezoom=QtWidgets.QSlider()

        #Initialize Widgets here:
        self.showVars.setChecked(False)
        self.variableselector.hide()
        # self._populateYvars(['P gain','Control signal','D gain','G gain','Error','Temperature','Pressure'])
        #Connect signals
        self.showVars.clicked.connect(self._showvarbar)
        self.toolbar.autoscale.connect(self.toolbar_active)
        self.Xchoices.currentIndexChanged.connect(self._xvarChanged)
        self.timezoom.sliderMoved['int'].connect(self._zoomChanged)


        #Setup Layout
        self._setupLayout()
        self.Xchoices.setCurrentText('Time')

        #TODO add multithreading here

    #
    def _setupLayout(self):
        self.topbar=QtWidgets.QHBoxLayout()
        # self.xaxisdropdown=QtWidgets.QHBoxLayout()
        # self.xaxisdropdown=QtWidgets.QFrame()
        # horzlayout=QtWidgets.QHBoxLayout(self.xaxisdropdown)
        # horzlayout.addStretch(1)
        # horzlayout.addWidget(self.Xlabel)
        # horzlayout.addWidget(self.Xchoices)
        # horzlayout.addStretch(1)
        # self.xaxisdropdown.addWidget(self.Xlabel)
        # self.xaxisdropdown.addWidget(self.Xchoices)

        #
        # xaxisSizePol=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # xaxisSizePol.setHorizontalStretch(30)
        #
        # navSizePol=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # navSizePol.setHorizontalStretch(33)
        #
        showVarSizePol=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        showVarSizePol.setHorizontalStretch(4)

        MainframeSizePol=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        MainframeSizePol.setHorizontalStretch(20)

        comboBoxSize=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Maximum)
        self.Xchoices.setSizePolicy(comboBoxSize)
        self.Xchoices.addItem("Time")
        font=QtGui.QFont()
        font.setPointSize(8)
        self.Xchoices.setFont(font)
        font.setPointSize(8)
        self.Xlabel.setFont(font)
        self.Ylabel.setFont(font)

        self.topbar.addWidget(self.toolbar)
        self.topbar.addStretch(1)
        self.topbar.addWidget(self.Xlabel)
        self.topbar.addWidget(self.Xchoices)
        # self.topbar.addStretch()
        self.topbar.addWidget(self.Ylabel)
        self.topbar.addWidget(self.showVars)
        self.mainframe=QtWidgets.QFrame()
        self.vbl=QtWidgets.QVBoxLayout(self.mainframe)
        self.vbl.addLayout(self.topbar)
        self.vbl.addWidget(self.canvas)
        self.mainframe.setSizePolicy(MainframeSizePol)
        self.variableselector.setSizePolicy(showVarSizePol)
        self.hbl=QtWidgets.QHBoxLayout()
        self.hbl.addWidget(self.mainframe)
        self.hbl.addWidget(self.timezoom)
        self.hbl.addWidget(self.variableselector)
        self.setLayout(self.hbl)

    def _showvarbar(self):
        if self.showVars.isChecked():
            self.variableselector.show()
        else:
            self.variableselector.hide()
    def toolbar_active(self,active):
        print('nav pressed')
        #pass the signal onto the plotter class
        self.auto_scale.emit(active)

    def populateVariables(self,names):
        header=QtWidgets.QHBoxLayout()
        left=QtWidgets.QLabel('L')
        center=QtWidgets.QLabel('Vars')
        right=QtWidgets.QLabel('R')
        font = QtGui.QFont()
        font.setPointSize(10)
        # font.setBold(True)
        left.setFont(font)
        right.setFont(font)
        center.setFont(font)
        header.addWidget(left)
        header.addStretch(1)
        header.addWidget(center)
        header.addStretch(1)
        header.addWidget(right)
        self.variableselectorlayout.addLayout(header)
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.variableselectorlayout.addWidget(line)
        if isinstance(names, list):
            for elem in names:
                self._addYvar(elem)
        self.variableselectorlayout.addStretch(1)


    def _addYvar(self,name):
        # index=len(self.yvars)
        index=len(self.yvarsL)
        rowhbox=QtWidgets.QHBoxLayout()
        cboxL=QtWidgets.QCheckBox()
        cboxL.setObjectName(str(index))
        cboxL.setChecked(True)
        cboxR=QtWidgets.QCheckBox()
        cboxR.setObjectName(str(index))
        cboxR.setChecked(False)

        cboxL.clicked['bool'].connect(self._yvarLChecked)
        cboxR.clicked['bool'].connect(self._yvarRChecked)



        label=QtWidgets.QLabel(name)
        font=QtGui.QFont()
        font.setPointSize(8)
        label.setFont(font)
        rowhbox.addWidget(cboxL)
        rowhbox.addStretch(1)
        rowhbox.addWidget(label)
        rowhbox.addStretch(1)
        rowhbox.addWidget(cboxR)
        self.variableselectorlayout.addLayout(rowhbox)
        self.Xchoices.addItem(name)
        self.yvarsL.append(cboxL)
        self.yvarsR.append(cboxR)

    def _yvarLChecked(self,state,*args):
        index=int(self.sender().objectName())
        if state is True:
            self.yvarsR[index].setChecked(False)
            # self.yvarsRight_sig.emit([index,False])

        self.yvarsLeft_sig.emit([index,state])
        print(state)
        print('here')

    def _yvarRChecked(self,state,*args):
        index = int(self.sender().objectName())
        if state is True:
            self.yvarsL[index].setChecked(False)
            # self.yvarsLeft_sig.emit([index, False])

        self.yvarsRight_sig.emit([index,state])

        print(state)
        print('here')

    def _xvarChanged(self,index,*args):
        print(self.sender().objectName())
        text=self.Xchoices.currentText()
        self.xvariable_sig.emit([index,text])
        # print('here'+str(index))

    def _zoomChanged(self,scale):
        self.zoomsig.emit(scale)

    def reapplyformatting(self):
        # self.canvas.ax.minorticks_on()
        self.canvas.ax.grid(b=True, which='major', color='silver', linestyle='-')
        # self.canvas.ax.grid(b=True, which='minor', color='gainsboro', linestyle='--')
        self.canvas.fig.tight_layout()
        self.canvas.fig.set_tight_layout(True)


class myNavToolbar(NavigationToolbar):
    autoscale = pyqtSignal(int, name='disautoscale')
    NavigationToolbar.toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        #('Back', 'Back to previous view', 'back', 'back'),
        #('Forward', 'Forward to next view', 'forward', 'forward'),
        #(None, None, None, None),
        ('Pan',
         'Left button pans, Right button zooms\n'
         'x/y fixes axis, CTRL fixes aspect',
         'move', 'pan'),
        ('Zoom', 'Zoom to rectangle\nx/y fixes axis, CTRL fixes aspect',
         'zoom_to_rect', 'zoom'),
        #('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
        #(None, None, None, None),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
      )

    def __init__(self, *args,**kwargs):
        super(myNavToolbar,self).__init__(*args,*kwargs)

    def _update_buttons_checked(self):
        if 'pan' in self._actions:
            self._actions['pan'].setChecked(self.mode.name == 'PAN')

        if 'zoom' in self._actions:
            self._actions['zoom'].setChecked(self.mode.name == 'ZOOM')

        if self.mode.name=='PAN' or self.mode.name=='ZOOM':
            self.autoscale.emit(1)
        else:
            self.autoscale.emit(0)


