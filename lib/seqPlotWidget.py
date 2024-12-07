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
        self.initUI()

        self.curves = curves
        self.names = names

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


    def replotCurves(self):
        self.plot.clear()
        for (ic,c) in enumerate(self.curves):
            self.plotData(self.x,self.y[ic],c,self.names[ic])
            

    def plotData(self,x,y,color,name):
        curve = self.plot.plot(name=name)
        curve.setData(x,y,pen=pg.mkPen(color, width=2))
        
    def setData(self,xValues,yValues):
        self.x = xValues
        self.y = yValues
        self.replotCurves()
