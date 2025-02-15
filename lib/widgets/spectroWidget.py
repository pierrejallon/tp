import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal,QThread,QDateTime,QTimer
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication,QMessageBox,QWidget,QLayout,QHBoxLayout,QDateTimeEdit,QButtonGroup,QPushButton,QRadioButton
import pyqtgraph as pg
import numpy as np
import logging

class spectroWidget(QWidget):
    
    def __init__(self,memorySize,Te,Fe_max,FFTSize):
        super(spectroWidget, self).__init__()

        self.memorySize = memorySize # in seconds
        self.samplingTime = Te # in seconds
        self.Fe_max = Fe_max # in seconds
        self.FFTSize = FFTSize
        self.nbDataReceived = -self.memorySize * self.samplingTime

        self.img_array = np.zeros(((int)(self.memorySize*self.samplingTime), int(FFTSize)))
        self.initUI()


    def __del__(self):
        if (self.timer):
            self.timer.stop()

    def initUI(self):   

        vbox = QHBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        self.setLayout(vbox)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        plotWidget = pg.GraphicsLayoutWidget()
        vbox.addWidget(plotWidget)

        self.plot = plotWidget.addPlot()
        # self.plot.setLabel("bottom", "Frequency", units="Hz")
        # self.plot.setLabel("left", "Time")

        # Item for displaying image data
        self.img = pg.ImageItem()
        self.plot.addItem(self.img)

        # Add a histogram with which to control the gradient of the image
        hist = pg.HistogramLUTItem()
        # Link the histogram to the image
        hist.gradient.loadPreset("flame")
        hist.setImageItem(self.img)
        # If you don't add the histogram to the window, it stays invisible, but I find it useful.
        plotWidget.addItem(hist)

        self.x = np.arange(-1.0*(int)(self.memorySize*self.samplingTime),0)
        self.y = np.arange(-0.5*self.FFTSize,0.5*self.FFTSize)

        x_scale = (self.x[-1] - self.x[0])/(self.x.shape[0]-1) if self.x.shape[0] > 1 else 1.0
        y_scale = (self.y[-1] - self.y[0])/(self.y.shape[0]-1) if self.y.shape[0] > 1 else 1.0

        self.plot.setLimits(xMin=self.x[0] - x_scale/2, xMax=self.x[-1] + x_scale/2,
                                yMin=self.y[0] - y_scale/2, yMax=self.y[-1] + y_scale/2)

        self.img.resetTransform()
        self.img.scale(x_scale, y_scale * self.Fe_max/self.FFTSize)
        self.img.setPos(self.x[0] - x_scale/2, (self.y[0] - y_scale/2)* self.Fe_max/self.FFTSize)

        self.plot.setLabel('left', 'Frequency', units='Hz')
        self.plot.setLabel('bottom', 'Time', units='s')


        self.timer=QTimer()
        self.timer.timeout.connect(self.replotCurves)
        self.timer.start(300)

    def clear(self):
        self.waterfallImg = pg.ImageItem()
        # self.waterfallImg.scale((data_storage.x[-1] - data_storage.x[0]) / len(data_storage.x), 1)
        self.plot.clear()
        self.plot.addItem(self.waterfallImg)

    def setFe(self,Fe):
        self.Fe_max = Fe

        self.x = np.arange(-1.0*(int)(self.memorySize*self.samplingTime),0)
        self.y = np.arange(-0.5*self.FFTSize,0.5*self.FFTSize)

        x_scale = (self.x[-1] - self.x[0])/(self.x.shape[0]-1) if self.x.shape[0] > 1 else 1.0
        y_scale = (self.y[-1] - self.y[0])/(self.y.shape[0]-1) if self.y.shape[0] > 1 else 1.0

        self.plot.setLimits(xMin=self.x[0] - x_scale/2, xMax=self.x[-1] + x_scale/2,
                                yMin=self.y[0] - y_scale/2, yMax=self.y[-1] + y_scale/2)

        self.img.resetTransform()
        self.img.scale(x_scale, y_scale * self.Fe_max/self.FFTSize)
        self.img.setPos(self.x[0] - x_scale/2, (self.y[0] - y_scale/2)* self.Fe_max/self.FFTSize)

    def replotCurves(self):
        self.img.setImage(self.img_array)
        xAxis = self.plot.getAxis('bottom')
        xAxis.setRange(self.nbDataReceived,self.nbDataReceived+self.memorySize*self.samplingTime)
        
    def addFFTData(self,FFTValues):
        # add fft values
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = FFTValues

        self.nbDataReceived = self.nbDataReceived + self.samplingTime


