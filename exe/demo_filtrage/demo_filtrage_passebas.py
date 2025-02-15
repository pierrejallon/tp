# File: main.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow,QVBoxLayout,QHBoxLayout,QTabWidget,QApplication,QPushButton,QMessageBox,QLayout,QCheckBox,QComboBox,QLabel, QTableWidget,QWidget,QSpinBox,QDockWidget,QTableWidgetItem,QDateEdit,QLineEdit
from PySide2.QtCore import QFile,Signal,QDateTime,QDate,QTimer
from PySide2 import QtCore, QtGui

import logging
from lib.widgets.qtLogger import qtLoggingHandler, logWidget
from lib.widgets.plotWidget import plotWidget
from lib.widgets.seqPlotWidget import seqPlotWidget
from lib.sigpro.seqAcquisition import seqAcquisition
from lib.widgets.demo_filtrage_options.demoFiltragePBIdealOptions import demoFiltrageOptionsWidget
from lib.sigpro.liveFilter import LiveLFilter
from lib.widgets.card.cardWidget import cardWidget


import math
import numpy as np
from scipy import signal

class mainWindow(QMainWindow):
    def __init__(self,handler):
        # QMainWindow.__init__(self)
        super(mainWindow, self).__init__()

        mainWidget=QWidget(self)
        self.setCentralWidget(mainWidget)

        vbox = QVBoxLayout()
        mainWidget.setLayout(vbox)  

        ################
        # Add the card status widget to interface
        ################
        self.status = cardWidget()
        dockLeft = QDockWidget("Card status", self)
        dockLeft.setWidget(self.status)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        self.status.connectionSet.connect(self.setFe)
        self.status.dataReceivedSig.connect(self.dataReceived)

        ################
        # Add widget for filter related options
        ################ 
        self.options = demoFiltrageOptionsWidget()
        dockLeft = QDockWidget("Options", self)
        dockLeft.setWidget(self.options)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        self.options.LPRB.toggled.connect ( self.changeFilter )
        self.options.HPRB.toggled.connect ( self.changeFilter ) 
        self.options.fc.valueChanged.connect( self.changeFilter )

        ################
        # init counter for time tracking
        ################
        self.nbDataReceived = 0
        self.fe = 1000

        ################
        # Set up GUI for data display
        ################
        wid = QWidget()
        vbox = QHBoxLayout()
        wid.setLayout(vbox)  

        self.rawPlotWidget = plotWidget(1,1.0 / self.fe,['b','r'],['x','y'])
        self.fftPlot = seqPlotWidget(['b','r'],['X(f)','Y(f)'])

        wid.layout().addWidget(self.rawPlotWidget)
        wid.layout().addWidget(self.fftPlot)
        mainWidget.layout().addWidget(wid)

        ################
        # Signal processing parameters
        ################
        # time window length in seconds (for FFT analysis)
        self.TWLength = 1

        # time window
        self.seqCutter = seqAcquisition(self.seqReceived,self.TWLength,1.0,self.fe,3)

        # init filter
        self.filter_b, self.filter_a = signal.butter(8, self.options.fc.value(), 'low', fs=self.fe)
        self.f = LiveLFilter(self.filter_b,self.filter_a)

    #############
    # Interface related functions
    #############
    def changeFilter(self):
        if (self.options.LPRB.isChecked()):
            self.filter_b, self.filter_a = signal.butter(8, self.options.fc.value(), 'low',  fs=self.fe)
        else:
            self.filter_b, self.filter_a = signal.butter(8, self.options.fc.value(), 'high',  fs=self.fe)
        self.f.changeFilter(self.filter_b,self.filter_a)
        self.seqCutter.reset()
        return 
    
    # called when sampling frequence is defined from card interface
    def setFe(self,Fe):
        self.fe = Fe
        self.filter_b, self.filter_a = signal.butter(8, self.options.fc.value(), 'low', fs=self.fe)
        self.f = LiveLFilter(self.filter_b,self.filter_a)
        self.rawPlotWidget.setFe(Fe)
        self.seqCutter.setFe(Fe)

    #############
    # data related functions
    #############
    def dataReceived(self,ch0,ch1):
        # filter signals
        fV = [0] * len(ch0)
        for (ic,v) in enumerate(ch0):
            fV[ic] = self.f.process(v)
        
        # plot signals
        self.rawPlotWidget.addDataArray([ch0,fV])

        # compute time
        tps = [(k+self.nbDataReceived) * 1.0/self.fe for k in range(len(ch0))]
        self.nbDataReceived = self.nbDataReceived + len(ch0)

        # add to sequence cutter
        self.seqCutter.arrayReceived([tps,ch0,fV])

    def seqReceived(self,seq):
        # compute and plot FFT
        p = np.fft.fftshift( np.fft.fft(seq[1,:],4096))
        p2 = np.fft.fftshift( np.fft.fft(seq[2,:],4096))
        f = [(k/len(p) -0.5) * self.fe for k in range(len(p))] 
        # plot fft
        self.fftPlot.setData(f,[np.abs(p),np.abs(p2)])
        return 


if __name__ == "__main__":

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = qtLoggingHandler()
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(threadName)-30.30s]   %(message)s")
    handler.setFormatter(log_formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    os.environ['KMP_DUPLICATE_LIB_OK']='True'

    app = QApplication(sys.argv)

    """
    # GO GO GO
    """
    mW = mainWindow(handler)
    mW.show()
    sys.exit(app.exec_())

