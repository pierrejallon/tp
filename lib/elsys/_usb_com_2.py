#==============================================================================
# Imports
#==============================================================================
from threading import Lock
import serial
from time import sleep, time
from .consts import *
from .file_manipulation import *
from ._usb_protocol_to_board import *

#==============================================================================
# Constants
#==============================================================================

# Length of the buffer to send for generation
PAYLOAD_LEN_BY_FREQUENCY_FOR_GENERATION_ONLY = [4096, 8192, 8192, 16384, 16384]

# Length of the buffer to send for acquisition and generation
PAYLOAD_LEN_BY_FREQUENCY_FOR_ACQUISITION_GENERATION = 8192

# Coefficient between 8 and 32 bits for data conversion
DATA_CONVERSION_COEFF = 4

#==============================================================================
# Global variables
#==============================================================================

# Fifo buffer to store samples before sending
fifo = []

# Lock to protect fifo buffer
fifo_mutex = Lock()

# Is the com port connection open
com_open = True

# Lock to protect com port connection status
com_mutex = Lock()

#==============================================================================
# Functions
#==============================================================================

"""
"" Initialize generation variables
"" Parameters : sampling_frequency_index : Index of sampling frequency of the signal (0 to 4)
""              channels_out : Generation channels usages
""              generation_only : True if this function is used in generation only,
                                  False if used in acquisition and generation
"" Returns the length of the payload to generate, the max time to sleep before new generation in seconds,
""         the numbers of used output channels and the sampling frequency
"""
def __generation_init(sampling_frequency_index: int, channels_out: list[bool], generation_only: bool = True) \
    -> tuple[int, float, int, float]:

    channels_count = 0
    for c in channels_out:
        if c:
            channels_count += 1

    sampling_frequency = FREQUENCIES_FROM_INDEX[sampling_frequency_index]

    if not generation_only:
        payload_len = PAYLOAD_LEN_BY_FREQUENCY_FOR_ACQUISITION_GENERATION
    else:
        payload_len = PAYLOAD_LEN_BY_FREQUENCY_FOR_GENERATION_ONLY[sampling_frequency_index]
    generation_loop_duration = payload_len/(channels_count*sampling_frequency*DATA_CONVERSION_COEFF)
    return payload_len, generation_loop_duration, channels_count, sampling_frequency

"""
"" Send samples to output ports
"" Parameters : com : com port to use
""              generation_loop_duration : max time to sleep before new generation in seconds
""              payload_len : length of the payload to generate
"""
def __generation_loop(com: serial.Serial,
                      generation_loop_duration: float,
                      payload_len: int):
    send_start_time: float = time()
    __send_fifo_by_blocks(com, payload_len)
    send_end_time: float = time() - send_start_time
    sleep(max(generation_loop_duration-send_end_time, 0))

"""
"" Send samples to output ports
"" Parameters : com : com port to use
""              generation_loop_duration : max time to sleep before new generation in seconds
"""
def __asynchronous_generation_loop(com: serial.Serial, generation_loop_duration: float):
    send_start_time: float = time()
    __send_entire_fifo(com)
    send_end_time: float = time() - send_start_time
    sleep(max(generation_loop_duration-send_end_time-0.020, 0))

"""
"" Send samples in the FIFO buffer by little blocks to the port com
"" Parameters : com : com port to use
""              payload_len : length of the payload to generate
"""
def __send_fifo_by_blocks(com: serial.Serial, payload_len: int):
    global fifo_mutex
    if not fifo_mutex.acquire():
        return
    try:
        global fifo
        if len(fifo) > payload_len:
            com.write(fifo[:payload_len])
            fifo = fifo[payload_len:]
        else:
            com.write(fifo)
            fifo = []
    except Exception:
        print('timeout !')
    finally:
        fifo_mutex.release()

"""
"" Send all samples in the FIFO buffer at once to the port com
"" Parameters : com : com port to use
"""
def __send_entire_fifo(com: serial.Serial):
    global fifo_mutex
    if not fifo_mutex.acquire():
        return

    try:
        global fifo
        rest = len(fifo)%64
        com.write(fifo[:len(fifo)-rest])
        fifo = fifo[len(fifo)-rest:]
    except Exception:
        print('timeout !')
    finally:
        fifo_mutex.release()

"""
"" Generate payload from data in a file and send it to a port com
"" Parameters : com : com port to use
""              file_name : Name of the file to read
""              channels_out : Generation channels usages
""              numeric_filters : filters to apply to the acquired signals for each output channel
"""
def generation(com: serial.Serial,
               file_name: str,
               sampling_frequency_index: int,
               channels_out: list[bool],
               numeric_filters: list[callable]):

    try:
        print('Launching write data...')

        sampling_frequency: float = FREQUENCIES_FROM_INDEX[sampling_frequency_index]
        file_frequency, file_samples = read_samples_from_file(file_name)
        if (file_frequency != FREQUENCIES_FROM_INDEX[FREQUENCY_100HZ]) \
        and (file_frequency != FREQUENCIES_FROM_INDEX[FREQUENCY_500HZ]) \
        and (file_frequency != FREQUENCIES_FROM_INDEX[FREQUENCY_1KHZ]) \
        and (file_frequency != FREQUENCIES_FROM_INDEX[FREQUENCY_2KHZ]) \
        and (file_frequency != FREQUENCIES_FROM_INDEX[FREQUENCY_10KHZ]):
            print('Error : Invalid frequency', file_frequency, 'retrieved from file ' + file_name
                  + '. Stopping generation')
            return 1
        elif file_frequency != sampling_frequency:
            print('Error : Different sampling frequencies between file and configuration (' + str(file_frequency)
                  + ' != ' + str(sampling_frequency) + ')')
            return 1

        payload_len, generation_loop_duration, channels_count, _ = \
            __generation_init(sampling_frequency_index, channels_out)
        nb_buffers_before_sleep = \
            int(sampling_frequency*channels_count//(payload_len//PAYLOAD_LEN_BY_FREQUENCY_FOR_GENERATION_ONLY[0])//400)

        add_samples_to_fifo(file_samples, channels_out, numeric_filters)

        if not is_event_set():
            print('writing samples')

            for _ in range(nb_buffers_before_sleep):
                if is_event_set():
                    break
                __send_fifo_by_blocks(com, payload_len)

            while len(fifo) > 0 and not is_event_set():
                __generation_loop(com, generation_loop_duration, payload_len)
            print('samples written correctly')
    except serial.SerialException:
        print('Unexpected serial error. Stopping generation')
        set_com_closed()

"""
"" Generate payload from data in the FIFO buffer and send it to a port com
"" Parameters : com : com port to use
""              sampling_frequency_index : Index of sampling frequency of the signal (0, 1 or 2)
""              channels_out : Generation channels usages
"""
def asynchronous_generation(com: serial.Serial,
                            sampling_frequency_index: int,
                            channels_out: list[bool]):
    global fifo

    try:

        payload_len, generation_loop_duration, channels_count, sampling_frequency = \
            __generation_init(sampling_frequency_index, channels_out, False)
        payload_start_sending_len = int(payload_len*sampling_frequency*channels_count//800)

        print('Launching continous write data...')

        while len(fifo) < payload_start_sending_len and not is_event_set() and is_com_open():
            sleep(0.01)

        while not is_event_set() and is_com_open():
            i: int = 0
            while len(fifo) == 0 and i < 100:
                sleep(0.001)
                i += 1
            if len(fifo) > 0:
               __asynchronous_generation_loop(com, generation_loop_duration)
        if not is_com_open():
            print('Unexpected serial error. Stopping generation')
        if is_event_set():
            print('Interruption caught during generation. Stopping thread')
    except serial.SerialException:
        print('Unexpected serial error. Stopping generation')
        set_com_closed()

"""
"" Add formatted samples to the sending FIFO buffer
"" Parameter : payload : the formatted samples
"""
def __add_payload(payload: list[int]):
    global fifo_mutex
    if not fifo_mutex.acquire():
        return

    try:
        global fifo

        fifo.extend(payload)
    except Exception:
        print('error')
    finally:
        fifo_mutex.release()

"""
"" Format samples for sending and add them to the FIFO buffer
"" Parameters : samples : samples to format by input channel
                filters : filter functions for each output channel
"""
def add_samples_to_fifo(samples: list[list[int]], channels_out: list[bool], filters: list[callable]):

    payload: list[int] = build_payload(samples, filters, channels_out)
    __add_payload(payload)

def is_com_open():
    global com_mutex
    new_com_open = False
    if not com_mutex.acquire():
        return
    try:
        global com_open
        new_com_open = com_open
    except Exception:
        pass
    finally:
        com_mutex.release()
        return new_com_open

def set_com_closed():
    global com_mutex
    if not com_mutex.acquire():
        return
    try:
        global com_open
        com_open = False
    except Exception:
        pass
    finally:
        com_mutex.release()
