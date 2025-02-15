# File: main.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow,QVBoxLayout,QTabWidget,QApplication,QPushButton,QMessageBox,QLayout,QCheckBox,QComboBox,QLabel, QTableWidget,QWidget,QSpinBox,QDockWidget,QTableWidgetItem,QDateEdit,QLineEdit
from PySide2.QtCore import QFile,Signal,QDateTime,QDate,QTimer
from PySide2 import QtCore, QtGui

import logging
from lib.widgets.card.cardWidget import cardWidget
from lib.widgets.qtLogger import qtLoggingHandler, logWidget
from lib.widgets.plotWidget import plotWidget
from lib.widgets.seqPlotWidget import seqPlotWidget
from lib.widgets.spectroWidget import spectroWidget
from lib.sigpro.seqAcquisition import seqAcquisition
from lib.widgets.demo_fft_options.demoFFTOptions import demoFFTOptionsWidget

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
        # init counter for time tracking
        ################
        self.nbDataReceived = 0
        self.fe = 1000

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
        # Add demo FFT options in interface (only time window length)
        ################
        self.options = demoFFTOptionsWidget()
        dockLeft = QDockWidget("Options", self)
        dockLeft.setWidget(self.options)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,dockLeft)

        self.TW = self.options.tw.value() 
        self.options.tw.valueChanged.connect( self.changeTW )

        ################
        # Setup GUI items and curves
        ################
        self.tab = QTabWidget()
        mainWidget.layout().addWidget(self.tab)

        self.rawPlotWidget = plotWidget(1,1/1000,['b'],['x'])
        self.tab.addTab(self.rawPlotWidget,"Signaux bruts")

        self.seqPlot = seqPlotWidget(['b'],['Bloc'])
        self.tab.addTab(self.seqPlot,"Sequence")

        self.fftPlot = seqPlotWidget(['b'],['FFT'])
        self.tab.addTab(self.fftPlot,"FFT")

        self.SW = spectroWidget(20,1,self.fe,4096)
        self.tab.addTab(self.SW,"Spectrogram")

        ################
        # Initiate object to generate time window based on received data
        # Parameters:
        # 1. When a time window is ready, function seqReceived is called 
        # 2. Time window length is 1 sec
        # 3. Delta between time window is 0.25 --> 1 time window is generated every 250 ms
        # 4. Sampling period is 1/self.fe
        # 5. 2 signals are used to generate time window: time & data received from card
        ################
        self.timeShiftBetweenTW_inSec = 0.25
        self.seqCutter = seqAcquisition(self.seqReceived,1.0,self.timeShiftBetweenTW_inSec,1/self.fe,2)

    #############
    # Interface related functions
    #############
    # called when time window is changed from interface
    def changeTW(self,tw):
        self.TW = self.options.tw.value() 
        self.seqCutter.changeTW( self.TW,self.timeShiftBetweenTW_inSec,self.fe )

    # called when sampling frequence is defined from card interface
    def setFe(self,Fe):
        self.fe = Fe
        self.rawPlotWidget.setFe(Fe)
        self.seqCutter.setFe(Fe)
        self.SW.setFe(Fe)


    #############
    # data related functions
    #############
    # called when data is received from card
    def dataReceived(self,ch0,ch1):
        # display raw signals
        self.rawPlotWidget.addDataArray([ch0])

        # compute time
        tps = [(k+self.nbDataReceived) * 1.0/self.fe for k in range(len(ch0))]
        self.nbDataReceived = self.nbDataReceived + len(ch0)

        # cut signal into sequence
        self.seqCutter.arrayReceived([tps,ch0])

    # called when a time window is received
    def seqReceived(self,seq):

        # plot
        self.seqPlot.setData(seq[0,:],[seq[1,:]])

        # compute and plot FFT
        # decimate a factor 10
        # p = np.fft.fftshift( np.fft.fft(seq[1,0:-1:10],4096))
        # f = [(k/len(p) -0.5) * self.fe/10 for k in range(len(p))] 

        p = np.fft.fftshift( np.fft.fft(seq[1,:],4096))
        f = [(k/len(p) -0.5) * self.fe for k in range(len(p))] 

        # plot fft
        self.fftPlot.setData(f,[np.abs(p)])

        # update spectrogram
        self.SW.addFFTData(np.abs(p))



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

