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
        self.nbSec = nbSec
        self.nbSamples = (int)(nbSec * samplingFreq)
        self.rawOffset = offset
        self.offset = offset  * samplingFreq
        self.size = size
        self.values = np.zeros( (self.size,self.nbSamples*2) )

    def setFe(self,Fe):
        self.nbSamples = (int)(self.nbSec * Fe)
        self.offset = self.rawOffset  * Fe
        self.reset()

    def reset(self):
        self.nbFrameReceived = 0
        self.values = np.zeros( (self.size,self.nbSamples*2) )

    def changeTW(self,nbSec,offset,samplingFreq):
        self.nbFrameReceived = 0
        self.nbSamples = int(nbSec * samplingFreq)
        self.offset = int(offset  * samplingFreq)
        self.values = np.zeros( (self.size,self.nbSamples*2) )

    def changeOffsetInSamples(self,offset):
        self.offset = offset  

    def arrayReceived(self,newArray):

        # # time management
        l = len(newArray[0])
        if (l==0):
            return 
        # if l > len(self.values[0,:])-1:
        #     l = len(self.values[0,:]) - 2
        #     for (ic,c) in enumerate(self.values):
        #         newArray[ic][:] = newArray[ic][-l:]

        for (ic,c) in enumerate(self.values):
            # print(self.values[ic,-l:])
            self.values[ic,:-l] = self.values[ic,l:] 
            self.values[ic,-l:] = newArray[ic][:]

        self.nbFrameReceived = self.nbFrameReceived + l
        if (self.nbFrameReceived>self.offset):
            self.seqReadyCB( self.values[:,0:self.nbSamples] ) 
            self.nbFrameReceived = 0