from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,Signal
from PySide2 import QtCore, QtGui,QtWidgets
from PySide2.QtWidgets import QApplication,QWidget,QLayout,QListWidget,QVBoxLayout
import logging


class QSignaler(QtCore.QObject):
    log_message = QtCore.Signal(object)

class qtLoggingHandler(QtCore.QObject, logging.Handler):
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)
        self.emitter = QSignaler()

    def emit(self, logRecord):
        # This is intended to be logging.Handler 
        # implementation of emit, not the QObject one
        self.format(logRecord)

        time = ""
        level = ""
        msg = ""
        if (hasattr(logRecord, 'asctime')):
            time = logRecord.asctime
        
        if (hasattr(logRecord, 'levelname')):
            level = logRecord.levelname

        msg = "{0}".format(logRecord.getMessage())
        self.emitter.log_message.emit([time,level,msg])


class logWidget(QtWidgets.QWidget):
    
    def __init__(self,handler):
        super(logWidget, self).__init__()
        self.initUI(handler)
        
    def initUI(self,handler):   

        ui_file = QFile("lib/widgets/logWidget.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.widget = loader.load(ui_file)
        ui_file.close()

        vbox = QVBoxLayout()
        vbox.addWidget(self.widget)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.lw = self.findChild(QListWidget,"listWidget")
        self.clearButton = self.findChild(QtCore.QObject,"pushButton")

        handler.emitter.log_message.connect(self.msgReceived)
        self.clearButton.clicked.connect(self.clearMsg)

    def msgReceived(self,data):
        str = "[{}] {}".format(data[0],data[2])
        if (data[1]== "CRITICAL"):
            str = "!!! [{}] {}".format(data[0],data[2])
        self.lw.addItem(str)

        if (data[1]== "DEBUG"):
            self.lw.item(self.lw.count()-1).setForeground(QtGui.QBrush(QtGui.QColor("#555555")))
        if (data[1]== "INFO"):
            self.lw.item(self.lw.count()-1).setForeground(QtGui.QBrush(QtGui.QColor("#0000FF")))
        if (data[1]== "WARNING"):
            self.lw.item(self.lw.count()-1).setForeground(QtGui.QBrush(QtGui.QColor("#FFA500")))
        if (data[1]== "ERROR"):
            self.lw.item(self.lw.count()-1).setForeground(QtGui.QBrush(QtGui.QColor("#FF0000")))
        if (data[1]== "CRITICAL"):
            self.lw.item(self.lw.count()-1).setForeground(QtGui.QBrush(QtGui.QColor("#FF0000")))
        self.lw.setCurrentItem(self.lw.item(self.lw.count()-1))

    def clearMsg(self):
        self.lw.clear()