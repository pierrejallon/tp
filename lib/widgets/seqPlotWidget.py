import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal,QThread,QDateTime,QTimer
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication,QMessageBox,QWidget,QLayout,QVBoxLayout,QDateTimeEdit,QButtonGroup,QPushButton,QRadioButton
import pyqtgraph as pg
import numpy as np
import logging

class seqPlotWidget(QWidget):
    
    def __init__(self,curves,names):
        super(seqPlotWidget, self).__init__()

        self.curves = curves
        self.names = names
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


    def replotCurves(self):
        for (ic,c) in enumerate(self.curves):
            self.curvesObj[ic].setData(self.x,self.y[ic],pen=pg.mkPen(c, width=2))

        # self.plot.clear()
        # for (ic,c) in enumerate(self.curves):
        #     self.plotData(self.x,self.y[ic],c,self.names[ic])
            

    # def plotData(self,x,y,color,name):
    #     curve = self.plot.plot(name=name)
    #     curve.setData(x,y,pen=pg.mkPen(color, width=2))
        
    def setData(self,xValues,yValues):
        self.x = xValues
        self.y = yValues
        self.replotCurves()

    def setUnitYRange(self):
        # self.plot.getAxis('left').p1.setXRange(5, 20, padding=0)
        self.plot.setRange(yRange=[-1,1])
