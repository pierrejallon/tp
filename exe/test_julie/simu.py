
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
from lib.sigpro.liveFilter import LiveLFilter
from lib.widgets.card.cardWidget import cardWidget

import math
import numpy as np
from scipy import signal

k=np.arange(-2,3,1)
b = 1.0/5*np.array(np.sinc(k/5))
b = np.array([1,1,1,1,1])

a = 1

w,H = signal.freqz(b,a,512, fs=1)
print(b)
       

# class mainWindow(QMainWindow):

#     def __init__(self,handler):
#         # QMainWindow.__init__(self)
#         super(mainWindow, self).__init__()

#         # mainWidget=QWidget(self)
#         self.seqPlot = seqPlotWidget(['b'],['rep freq'])
#         self.seqPlot.setData(np.array(w),[np.array(np.abs(H))])
#         self.setCentralWidget(self.seqPlot)        

#         # self.seqPlot.show()



# if __name__ == "__main__":

#     # logger = logging.getLogger()
#     # logger.setLevel(logging.INFO)

#     handler = qtLoggingHandler()
#     # log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(threadName)-30.30s]   %(message)s")
#     # handler.setFormatter(log_formatter)
#     # handler.setLevel(logging.DEBUG)
#     # logger.addHandler(handler)

#     # os.environ['KMP_DUPLICATE_LIB_OK']='True'

#     app = QApplication(sys.argv)

#     """
#     # GO GO GO
#     """
#     mW = mainWindow(handler)
#     mW.show()
#     sys.exit(app.exec_())

import matplotlib.pyplot as plt
plt.figure()
plt.plot(b)
plt.show()