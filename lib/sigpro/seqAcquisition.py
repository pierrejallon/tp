import sys
sys.path.append('./')
import time
import numpy as np

##############
# librarie to compute sequence of signals
##############

class seqAcquisition():

    def __init__(self,seqReadyCB,nbSec,offset,samplingFreq,size):
        self.seqReadyCB = seqReadyCB
        self.nbFrameReceived = 0
        self.nbSamples = (int)(nbSec * samplingFreq)
        self.offset = offset  * samplingFreq
        self.size = size
        self.values = np.zeros( (self.nbSamples,size) )

    def reset(self):
        self.nbFrameReceived = 0
        self.values = np.zeros( (self.nbSamples,self.size) )

    def changeTW(self,nbSec,offset,samplingFreq):
        self.nbFrameReceived = 0
        self.nbSamples = nbSec * samplingFreq
        self.offset = offset  * samplingFreq
        self.values = np.zeros( (self.nbSamples,self.size) )

    def changeOffsetInSamples(self,offset):
        self.offset = offset  

    def processArray(self,a,v):
        if (len(v)==self.size):
            a = np.vstack([a,v])
            a = np.delete(a,0,0)
        return a

    def dataReceived(self,newValues):
        self.values = self.processArray( self.values,newValues )
        self.nbFrameReceived = self.nbFrameReceived + 1
        if (self.nbFrameReceived>self.offset):
            self.seqReadyCB( self.values ) 
            self.nbFrameReceived = 0

