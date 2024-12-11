import lib.card.card_io as card_io
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtCore import QTimer,QObject,Signal
import logging
import gc

class qtCard(QtCore.QObject):

    dataReceived = QtCore.Signal(object,object)
    connectedStatus = QtCore.Signal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.card = 0

    def __del__(self):
        self.stopCard()

    def stopCard(self):
        if (not self.card == 0):
            self.card.stopCard()
            self.card = 0

    def listSerialPort(self):
        return card_io.listSerialPort()

    def findSerialPort(self):
        return card_io.findSerialPort()

    def connectToPort(self,port,samplingFreqIndex,antiAliasingFilterIndex):
        if ( self.card == 0):
            self.card = card_io.cardAcqui( port,samplingFreqIndex,antiAliasingFilterIndex )
            self.card.setDataReadyCB( self.dataAvailable )
            self.connectedStatus.emit(True)
        else:
            logging.warning("Already connected to a device")

    def disconnect(self):
        if ( not self.card == 0):
            self.card = 0
            self.card.connectedStatus.emit(False)
        else:
            logging.warning("Not connected to a device")

    def configAvailable(self,config):
        self.configReceived.emit(config)

    def dataAvailable(self,ch0,ch1):
        self.dataReceived.emit(ch0,ch1)

    def checkStatus(self):
        if ( not self.card == 0):
            if (self.card.isConnected):
                return True
            else:
                return False
        else:
            logging.warning("Not connected to a device")
            return False

    def startAcqui(self):
        if (self.checkStatus()):
            self.card.startAcqui()

    def stopAcqui(self):
        if (self.checkStatus()):
            self.card.stopCard()
