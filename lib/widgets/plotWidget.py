import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal,QThread,QDateTime,QTimer
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication,QMessageBox,QWidget,QLayout,QVBoxLayout,QDateTimeEdit,QButtonGroup,QPushButton,QRadioButton
import pyqtgraph as pg
import numpy as np
import logging

class plotWidget(QWidget):
    
    def __init__(self,memorySize,Te,curves,names):
        super(plotWidget, self).__init__()

        self.memorySize = memorySize # in seconds
        self.samplingTime = Te # in seconds
        self.curves = curves
        self.names = names

        self.time = np.linspace(-self.memorySize,0,num=(int)(self.memorySize/self.samplingTime))
        self.rawData = np.zeros((len(curves),(int)(self.memorySize/self.samplingTime)))

        self.initUI()

    def initUI(self):   

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        self.setLayout(vbox)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        plotData = pg.PlotWidget()
        vbox.addWidget(plotData)
        self.plot = plotData.plotItem
        self.plot.addLegend()

        self.curvesObj = [None] * len(self.curves)
        for (ic,c) in enumerate(self.curves):
            self.curvesObj[ic] =  self.plot.plot(name=self.names[ic]) 

        self.timer=QTimer()
        self.timer.timeout.connect(self.replotCurves)
        self.timer.start(50)

    def updateTW(self,TW):
        self.memorySize = TW
        self.time = np.linspace(-self.memorySize,0,num=(int)(self.memorySize/self.samplingTime))
        self.rawData = np.zeros((len(self.curves),(int)(self.memorySize/self.samplingTime)))
        self.replotCurves()

    def setFe(self,Fe):
        self.samplingTime = 1.0/Fe # in seconds

        self.time = np.linspace(-self.memorySize,0,num=(int)(self.memorySize/self.samplingTime))
        self.rawData = np.zeros((len(self.curves),(int)(self.memorySize/self.samplingTime)))
        self.replotCurves()

    def replotCurves(self):
        for (ic,c) in enumerate(self.curves):
            self.curvesObj[ic].setData(self.time,self.rawData[ic,:],pen=pg.mkPen(c, width=2))
        
    def addRawData(self,values):
        # time management
        self.time[:-1] = self.time[1:]   
        self.time[-1] = self.time[-2]+self.samplingTime

        for (ic,c) in enumerate(self.curves):
            self.rawData[ic,:-1] = self.rawData[ic,1:] 
            self.rawData[ic,-1] = values[ic]

    def addDataArray(self,values):
        # # time management
        l = len(values[0])
        if l > len(self.time)-1:
            l = len(self.time) - 2
            for (ic,c) in enumerate(self.curves):
                values[ic] = values[ic][-l:]
        self.time[:-l] = self.time[l:]   
        self.time[-l:] = [ self.time[-l-1] + (k+1) * self.samplingTime for k in range(l)]

        for (ic,c) in enumerate(self.curves):
            self.rawData[ic,:-l] = self.rawData[ic,l:] 
            self.rawData[ic,-l:] = values[ic]
