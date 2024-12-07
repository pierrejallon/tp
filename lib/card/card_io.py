import asyncio
import socket
import time
import signal
import threading
import struct
import serial 
import serial.tools.list_ports
import logging
from lib.card.card_constants import *

# Sampling frequency of the signal enumeration
FREQUENCY_100HZ = 0
FREQUENCY_500HZ = 1
FREQUENCY_1KHZ = 2
FREQUENCY_2KHZ = 3
FREQUENCY_10KHZ = 4

# Filters applied to the signal enumeration
FILTER_50HZ = 1
FILTER_250HZ = 2
FILTER_500HZ = 3
FILTER_1KHZ = 4
FILTER_5KHZ = 5
NO_FILTER = 6

def listSerialPort():
    return serial.tools.list_ports.comports()

def findSerialPort():
    """Get the name of the port that is connected to Arduino."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if p.vid and p.vid==1155:
            if p.pid and  p.pid==22336:
                if (not p.location):
                    port = p
                    return port.device
    return None

class cardAcqui():

    def __init__(self,port,samplingFreqIndex,antiAliasingFilterIndex):
        self.ser = serial.Serial(port=port,baudrate=2000000,timeout = 0.04)
        self.ser.set_buffer_size(rx_size = 65536, tx_size = 65536)
        self.isConnected = self.ser.is_open


        if (not self.isConnected):
            logging.info("not connected")
            return

        ##################
        # configure board        
        ##################
        self.corrupted_data = False
        self.reset_board()
        self.start_acquire(0)
        self.start_acquire(1)
        self.stop_gen(0)
        self.stop_gen(1)
        self.stop_gen(2)
        self.stop_gen(3)

        self.set_anti_aliasing_filter(0,antiAliasingFilterIndex)
        self.set_anti_aliasing_filter(1,antiAliasingFilterIndex)

        self.set_acquire_freq(samplingFreqIndex)
        # self.set_gen_freq(samplingFreqIndex)
        self.sampling_frequency_index = samplingFreqIndex


        ##################
        # start reading thread
        ##################

        self.isRunning = False
        self.dataReadyCB = 0     # callback for all kind of data

        # self.__runClient()
    def startAcqui(self):
        if (not self.isRunning):
            self.__runClient()

    def stopCard(self):
        if (self.isRunning):
            self.__stopClient() # stop reading thread

        if (self.isConnected):
            self.stop_acquire(0)
            self.stop_acquire(1)
            self.ser.close()
            self.isConnected = False

    def __del__(self):
        self.stopCard()
        
    ###############
    # Get status about client
    ###############
    def connected(self):
        return self.ser.is_open

    def running(self):
        return self.isRunning

    def setDataReadyCB(self,CB):
        self.dataReadyCB = CB

    ###############
    # I/O functions
    ###############


    def reset_board(self):
        COMMAND_RESET_VALUE = 0
        # create payload
        payload = [COMMAND_RESET_VALUE]
        # send payload on USB com
        self.ser.write(payload)

    def get_conf(self):
        # create payload
        COMMAND_GET_CONF_VALUE = 1
        payload = [COMMAND_GET_CONF_VALUE]
        # send payload on USB com
        self.ser.write(payload)

    def start_acquire(self, channel):
        # create payload
        COMMAND_START_ACQUIRE_VALUE = 11
        # print("start acquire {}".format(channel))
        payload = [COMMAND_START_ACQUIRE_VALUE, channel]
        # send payload on USB com
        self.ser.write(payload)

    def stop_acquire(self, channel):
        # create payload
        COMMAND_STOP_ACQUIRE_VALUE = 12
        payload = [COMMAND_STOP_ACQUIRE_VALUE, channel]
        # send payload on USB com
        self.ser.write(payload)

    def start_gen(self, channel):
        # create payload
        COMMAND_START_GEN_VALUE = 21
        payload = [COMMAND_START_GEN_VALUE, channel]
        # send payload on USB com
        self.ser.write(payload)

    def stop_gen(self, channel):
        # create payload
        COMMAND_STOP_GEN_VALUE = 22
        payload = [COMMAND_STOP_GEN_VALUE, channel]
        # send payload on USB com
        self.ser.write(payload)
        
    def set_acquire_freq(self, freq):
        # create payload
        COMMAND_SET_ACQUIRE_FREQ_VALUE = 13
        payload = [COMMAND_SET_ACQUIRE_FREQ_VALUE, freq]
        # send payload on USB com
        self.ser.write(payload)


    def set_gen_freq(self, freq):
        COMMAND_SET_GEN_FREQ_VALUE = 23
        # create payload
        payload = [COMMAND_SET_GEN_FREQ_VALUE, freq]
        # send payload on USB com
        self.ser.write(payload)
        
    def set_anti_aliasing_filter(self, channel, filter_number):
        # create payload
        COMMAND_SET_ANTI_ALIA_FILTER = 24

        payload = [COMMAND_SET_ANTI_ALIA_FILTER, channel | (filter_number * 16)]
        # send payload on USB com
        self.ser.write(payload)

    def is_payload_present(self, payload_len):
        return (self.ser.in_waiting >= payload_len)

    def read_data(self, channels_in, payload_len):
        array = self.ser.read(payload_len)
        return self.compute_data_samples(list(array), channels_in)

    def compute_data_samples(self,data, channels_in):
        samples_chann_1 = []
        samples_chann_2 = []
        index = 0
        while (index < len(data)):
            type = int(data[index])
            if type == TYPE_ACK_CONF:
                if self.corrupted_data:
                    self.corrupted_data = False
                time.sleep(1000)
                print("Success: ACK conf")
                break
            elif type == TYPE_NOK_CONF:
                if self.corrupted_data:
                    self.corrupted_data = False
                print("Error: NACK conf")
                break
            elif type == TYPE_SAMPLES_CHANN_1:
                if self.corrupted_data:
                    self.corrupted_data = False
                channel_in = channels_in[0]
                new_index, samples_chann_1 = self.extract_samples(data[index:], channel_in)
                index += new_index
            elif type == TYPE_SAMPLES_CHANN_2:
                if self.corrupted_data:
                    self.corrupted_data = False
                channel_in = channels_in[1]
                new_index, samples_chann_2 = self.extract_samples(data[index:], channel_in)
                index += new_index
            else:
                if not self.corrupted_data:
                    print("Error: Invalid data received. Waiting to retrieve correct data (if it takes a long time, " + \
                        "please stop this program and reset the board) ...")
                    self.corrupted_data = True
                break
        return samples_chann_1, samples_chann_2

    def extract_samples(self,data, channel_in):
        # extract samples from data
        l_SIGNAL_COEFF = 1.22

        samples = []
        len_samples = data[LEN_LSB_INDEX]
        len_samples += data[LEN_MIDDLE_BITS_1_INDEX] << BITS_8
        len_samples += data[LEN_MIDDLE_BITS_2_INDEX] << BITS_16
        len_samples += data[LEN_MSB_INDEX] << BITS_24
        i = 0
        if channel_in:
            for i in range(HEADER_SIZE, len_samples*NB_U8_IN_U32+HEADER_SIZE, NB_U8_IN_U32):
                if i+3 < len(data):
                    # uint32
                    sample = data[i+DATA_LSB_INDEX] + (data[i+DATA_MIDDLE_BITS_INDEX] << BITS_8) + (data[i] << BITS_16)
                    coeff = COEFF_POSITIVE if sample >= MEDIUM_VALUE_24_BITS else COEFF_NEGATIVE
                    diff = (sample - MEDIUM_VALUE_24_BITS)*coeff
                    sample = MEDIUM_VALUE_24_BITS+int(diff*coeff*l_SIGNAL_COEFF)
                    sample = (sample >> BITS_7)
                    sample += OFFSET_FIX_VALUE
                    if sample >= VALUE_OVERFLOW_16_BITS:
                        sample = VALUE_OVERFLOW_16_BITS-1
                    elif sample < 0:
                        sample = 0
                    samples.append(sample)
                else:
                    print("Error: Not enough data")
                    break
            i += NB_U8_IN_U32
        else:
            i = len_samples*4+HEADER_SIZE
        return i, samples

    def calibrationSamples(self,samples):
        # print(samples)
        c_s = [((value / (V_MAX * GAIN) * (VREF_PLUS - VREF_MINUS)) - VREF_MEDIUM) * SIGNAL_COEFF for value in samples]
        return c_s

    ###############
    # Client management functions
    ###############
    
    def __stopClient(self):
        if (self.isRunning):
            self.isRunning = False
            self.mainTh.join()

    def __do_runClient(self):
        # PAYLOAD_LENS_BY_FREQUENCY = [48, 254, 510, 1022, 2046]
        PAYLOAD_LENS_BY_FREQUENCY = [64, 256, 512, 1024, 1984]
        ch0 = []
        ch1 = []
        used_channels = 2
        payload_len = (PAYLOAD_LENS_BY_FREQUENCY[self.sampling_frequency_index]+2)*(4*used_channels)
        # print("{}-{}-{}".format(self.sampling_frequency_index,used_channels,payload_len))
        if (not self.isRunning):
            self.isRunning = True
            while self.isRunning:
                if self.is_payload_present(payload_len):
                    ch0, ch1 = self.read_data([True,True], payload_len)
                    ch0 = self.calibrationSamples(ch0)
                    ch1 = self.calibrationSamples(ch1)
                    if (self.dataReadyCB):
                        self.dataReadyCB(ch0,ch1)
                    time.sleep(0)
                else:
                    time.sleep(0)

    def __runClient(self):
        self.mainTh = threading.Thread(target=self.__do_runClient, args=())
        self.mainTh.setDaemon(True)
        self.mainTh.start()

