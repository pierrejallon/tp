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
from threading import Lock, Event

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
    resu = [None,None]
    for p in ports:
        if p.vid and p.vid==1155:
            if p.pid and  p.pid==22336:
                if (p.location): 
                    if (p.location=="1-3:x.2"):
                        port = p.device
                        resu[1] = port
                if (not p.location) | (p.location=="1-3:x.0"):
                    port = p.device
                    resu[0] = port
    return resu


class cardAcqui():

    def __init__(self,port,samplingFreqIndex,antiAliasingFilterIndex):
        # connect acquisition
        self.ser = serial.Serial(port=port[0],baudrate=2000000,timeout = 0.04)
        self.ser.set_buffer_size(rx_size = 65536, tx_size = 65536)
        self.isConnected = self.ser.is_open

        if (not self.isConnected):
            logging.info("not connected")
            return

        # connect generation
        self.serGene = serial.Serial(port=port[1],baudrate=2000000,timeout = 0.04)
        self.serGene.set_buffer_size(rx_size = 65536, tx_size = 65536)
        self.isConnected = self.serGene.is_open

        if (not self.isConnected):
            logging.info("not connected")
            return
        
        # data generation variables
        self.fifo = []
        self.fifo_mutex = Lock()

        self.event_mutex = Lock()
        self.last_channel_samples=[VALUE_0V, VALUE_0V, VALUE_0V, VALUE_0V]
        self.event = Event()
        self.single_info_message = False

        ##################
        # configure board        
        ##################
        self.corrupted_data = False
        self.reset_board()
        self.start_acquire(0)
        self.start_acquire(1)
        self.start_gen(0)
        self.start_gen(1)
        self.start_gen(2)
        self.start_gen(3)

        self.set_anti_aliasing_filter(0,antiAliasingFilterIndex)
        self.set_anti_aliasing_filter(1,antiAliasingFilterIndex)

        self.set_acquire_freq(samplingFreqIndex)
        self.set_gen_freq(samplingFreqIndex)
        self.sampling_frequency_index = samplingFreqIndex

        ##################
        # start reading thread
        ##################

        self.isAcquiRunning = False
        self.isGeneRunning = False
        self.dataReadyCB = 0     # callback for all kind of data

        # self.__runClient()
    def startAcqui(self):
        if (not self.isConnected):
            return
        if (not self.isAcquiRunning):
            self.__runAcqui()
        if (not self.isGeneRunning):
            self.__runGene()

    def stopCard(self):
        if (self.isAcquiRunning):
            self.__stopAcqui() # stop reading thread

        if (self.isGeneRunning):
            self.__stopGene()

        if (self.isConnected):
            self.stop_acquire(0)
            self.stop_acquire(1)
            self.stop_gen(1)
            self.stop_gen(1)
            self.stop_gen(1)
            self.stop_gen(1)
            self.ser.close()
            self.isConnected = False

    def __del__(self):
        self.stopCard()
        
    ###############
    # Get status about client
    ###############
    def connected(self):
        return self.ser.is_open

    def acquiRunning(self):
        return self.isAcquiRunning

    def setDataReadyCB(self,CB):
        self.dataReadyCB = CB

    ###############
    # Send data function
    ###############
    def sendSample(self,ch0,ch1,ch2,ch3):
        samples = [[],[],[],[]]
        samples[0][0] = ch0
        samples[1][0] = ch1
        samples[2][0] = ch2
        samples[3][0] = ch3
        self.add_samples_to_fifo(samples)
        return

    def sendBurst(self,ch0,ch1,ch2,ch3):
        samples = [[],[],[],[]]
        samples[0] = ch0
        samples[1] = ch1
        samples[2] = ch2
        samples[3] = ch3
        self.add_samples_to_fifo(samples)
        return

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

    ###############
    # internal for data reading
    ###############

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

    def VoltToCounts(self,v):
        # print(samples)
        c_s = [((value / SIGNAL_COEFF + VREF_MEDIUM) * (V_MAX * GAIN) / (VREF_PLUS - VREF_MINUS))  for value in v]
        return c_s
    
    ###############
    # internal for data generation
    ###############

    # mutex manipulation (usefull ??)
    def set_event(self,status: bool):
        if not self.event_mutex.acquire():
            return
        try:
            self.event.set() if status else self.event.clear()
        except Exception:
            pass
        finally:
            self.event_mutex.release()

    def is_event_set(self):
        if not self.event_mutex.acquire():
            return
        event_set = False
        try:
            event_set = self.event.is_set()
        except Exception:
            pass
        finally:
            self.event_mutex.release()
            return event_set
        

    def build_payload(self,samples: list[list[int]],channels_out: list[bool]) -> list[int]:
        usb_payload: list[int] = []
        channel_samples: list[list[int]] = [[], [], [], []]

        used_channels: list[bool] = []
        max_samples: int = 0
        for i in range(len(channels_out)):
            if channels_out[i]:
                used_channels.append(i)
                # channel_samples[i] = filters[i](list(samples[INDEX_CH_IN_1]), list(samples[INDEX_CH_IN_2]))
                ### Check here ? Convert values to byte ? 

                channel_samples[i] = self.VoltToCounts(samples[i])
                if channel_samples[i] == [] and not self.single_info_message:
                    print('Warning : With current acquired data and filters, channel ' + str(i+1)
                        + ' does not have output data')
                elif channel_samples != []:
                    # Revert to get last element as first in pop (faster)
                    channel_samples[i].reverse()
                    max_samples = max(max_samples, len(channel_samples[i]))

        self.single_info_message = True
        i: int = 0
        while i < max_samples and not self.is_event_set():
            for idx in used_channels:
                if channel_samples[idx] != []:
                    sample: int = channel_samples[idx].pop()
                    if sample >= VALUE_OVERFLOW_16_BITS:
                        sample = VALUE_OVERFLOW_16_BITS-1
                    elif sample < 0:
                        sample = 0
                    self.last_channel_samples[idx]=sample
                else :
                    sample = self.last_channel_samples[idx]
                usb_payload.append(int(sample) & MAX_8_BITS_VALUE)
                usb_payload.append(int(sample) >> BITS_8 & MAX_8_BITS_VALUE)
                # SPI header
                usb_payload.append(SPI_HEADERS[idx])
                # Padding
                usb_payload.append(PAYLOAD_PADDING)
            i += 1
        return usb_payload

    def __add_payload(self,payload: list[int]):
        if not self.fifo_mutex.acquire():
            return

        try:
            self.fifo.extend(payload)
        except Exception:
            print('error')
        finally:
            self.fifo_mutex.release()

    def add_samples_to_fifo(self,samples):
        channels_out = [True,True,True,True]
        payload: list[int] = self.build_payload(samples, channels_out)
        self.__add_payload(payload)

    def __generation_init(self,sampling_frequency_index: int, channels_out: list[bool], generation_only: bool = True) :

        channels_count = 0
        for c in channels_out:
            if c:
                channels_count += 1

        sampling_frequency = FREQUENCIES_FROM_INDEX[sampling_frequency_index]

        payload_len = PAYLOAD_LEN_BY_FREQUENCY_FOR_ACQUISITION_GENERATION
        # if not generation_only:
        #     payload_len = PAYLOAD_LEN_BY_FREQUENCY_FOR_ACQUISITION_GENERATION
        # else:
        #     payload_len = PAYLOAD_LEN_BY_FREQUENCY_FOR_GENERATION_ONLY[sampling_frequency_index]
        generation_loop_duration = payload_len/(channels_count*sampling_frequency*DATA_CONVERSION_COEFF)
        return payload_len, generation_loop_duration, channels_count, sampling_frequency

    def __send_entire_fifo(self):
        if not self.fifo_mutex.acquire():
            return
        try:
            rest = len(self.fifo)%64
            self.serGene.write(self.fifo[:len(self.fifo)-rest])
            self.fifo = self.fifo[len(self.fifo)-rest:]
        except Exception:
            print('timeout !')
        finally:
            self.fifo_mutex.release()

    ###############
    # Acquisition functions
    ###############
    
    def __stopAcqui(self):
        if (self.isAcquiRunning):
            self.isAcquiRunning = False
            self.mainTh.join()

    def __do_runAcqui(self):
        # PAYLOAD_LENS_BY_FREQUENCY = [48, 254, 510, 1022, 2046]
        PAYLOAD_LENS_BY_FREQUENCY = [64, 256, 512, 1024, 1984]
        ch0 = []
        ch1 = []
        used_channels = 2
        payload_len = (PAYLOAD_LENS_BY_FREQUENCY[self.sampling_frequency_index]+2)*(4*used_channels)
        # print("{}-{}-{}".format(self.sampling_frequency_index,used_channels,payload_len))
        if (not self.isAcquiRunning):
            self.isAcquiRunning = True
            while self.isAcquiRunning:
                if self.is_payload_present(payload_len):
                    ch0, ch1 = self.read_data([True,True], payload_len)
                    ch0 = self.calibrationSamples(ch0)
                    ch1 = self.calibrationSamples(ch1)
                    if (self.dataReadyCB):
                        self.dataReadyCB(ch0,ch1)
                    time.sleep(0)
                else:
                    time.sleep(0)

    def __runAcqui(self):
        self.mainTh = threading.Thread(target=self.__do_runAcqui, args=())
        self.mainTh.setDaemon(True)
        self.mainTh.start()


    ###############
    # Generation functions
    ###############

    def __stopGene(self):
        if (self.isGeneRunning):
            self.isGeneRunning = False
            self.geneTh.join()

    def __do_runGene(self):

        payload_len, generation_loop_duration, channels_count, sampling_frequency = \
            self.__generation_init(self.sampling_frequency_index, [True,True,True,True], False)
        payload_start_sending_len = int(payload_len*sampling_frequency*channels_count//800)

        if (not self.isGeneRunning):
            self.isGeneRunning = True
            while self.isGeneRunning:

                if ( len(self.fifo) >= payload_start_sending_len ):
                    if (not self.is_event_set()):
                        # print("generating data")
                        self.__send_entire_fifo()
                time.sleep(0)
                # try:


                #     while len(self.fifo) < payload_start_sending_len and not self.is_event_set() and self.serGene.is_open():
                #         time.sleep(0)

                #     while not self.is_event_set() and self.serGene.is_open():
                #         i: int = 0
                #         while len(self.fifo) == 0 and i < 100:
                #             time.sleep(0)
                #             i += 1
                #         if len(self.fifo) > 0:
                #             self.__send_entire_fifo(com)
                #             time.sleep(0)

                #     if not self.serGene.is_open():
                #         print('Unexpected serial error. Stopping generation')
                #     if self.is_event_set():
                #         print('Interruption caught during generation. Stopping thread')
                # except serial.SerialException:
                #     print('Unexpected serial error. Stopping generation')
                #     # set_com_closed()

                # time.sleep(0)

    def __runGene(self):
        self.geneTh = threading.Thread(target=self.__do_runGene, args=())
        self.geneTh.setDaemon(True)
        self.geneTh.start()

