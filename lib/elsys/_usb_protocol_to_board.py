from .consts import *
from threading import Lock, Event
import serial

#==============================================================================
# Constants
#==============================================================================

# SPI header for channel 0
SPI_HEADER_CH_0 = 0x1A

# SPI header for channel 1
SPI_HEADER_CH_1 = 0x19

# SPI header for channel 2
SPI_HEADER_CH_2 = 0x1C

# SPI header for channel 3
SPI_HEADER_CH_3 = 0x1B

# List pf SPI headers
SPI_HEADERS = [SPI_HEADER_CH_0, SPI_HEADER_CH_1, SPI_HEADER_CH_2, SPI_HEADER_CH_3]

# Signal borders
SIGNAL_MIN = 0
SIGNAL_MAX = 8388607

# Command to send
COMMAND_RESET_VALUE = 0
COMMAND_GET_CONF_VALUE = 1
COMMAND_START_ACQUIRE_VALUE = 11
COMMAND_STOP_ACQUIRE_VALUE = 12
COMMAND_SET_ACQUIRE_FREQ_VALUE = 13
COMMAND_START_GEN_VALUE = 21
COMMAND_STOP_GEN_VALUE = 22
COMMAND_SET_GEN_FREQ_VALUE = 23
COMMAND_SET_ANTI_ALIA_FILTER = 24

# Maximum value on 8 bits
MAX_8_BITS_VALUE = 255

# Padding to complete 32-bits int
PAYLOAD_PADDING = 0

#==============================================================================
# Global variables
#==============================================================================

# Last channel samples for padding if necessary
last_channel_samples=[VALUE_0V, VALUE_0V, VALUE_0V, VALUE_0V]

# Event to stop program execution
event = Event()

# Lock to protect event
event_mutex = Lock()

# Flag to show info message only once
single_info_message = False

#==============================================================================
# Functions
#==============================================================================

"""
Send command to reset board through com port
"" Parameters : com : com port to use
"""
def reset_board(com: serial.Serial):
    # create payload
    payload = [COMMAND_RESET_VALUE]
    # send payload on USB com
    com.write(payload)

"""
Send command to get current board configuration through com port
"" Parameters : com : com port to use
"""
def get_conf(com: serial.Serial):
    # create payload
    payload = [COMMAND_GET_CONF_VALUE]
    # send payload on USB com
    com.write(payload)

"""
Send command to start acquisition for a channel through com port
"" Parameters : com : com port to use
""              channel : channel for which activate acquisition
"""
def start_acquire(com: serial.Serial, channel: int):
    # create payload
    payload = [COMMAND_START_ACQUIRE_VALUE, channel]
    # send payload on USB com
    com.write(payload)

"""
Send command to stop acquisition for a channel through com port
"" Parameters : com : com port to use
""              channel : channel for which stop acquisition
"""
def stop_acquire(com: serial.Serial, channel: int):
    # create payload
    payload = [COMMAND_STOP_ACQUIRE_VALUE, channel]
    # send payload on USB com
    com.write(payload)

"""
Send command to set acquisition sampling frequency through com port
"" Parameters : com : com port to use
""              frequency : sampling frequency
"""
def set_acquire_freq(com: serial.Serial, frequency: float):
    # create payload
    payload = [COMMAND_SET_ACQUIRE_FREQ_VALUE, frequency]
    # send payload on USB com
    com.write(payload)

"""
Send command to start generation for a channel through com port
"" Parameters : com : com port to use
""              channel : channel for which activate generation
"""
def start_gen(com: serial.Serial, channel: int):
    # create payload
    payload = [COMMAND_START_GEN_VALUE, channel]
    # send payload on USB com
    com.write(payload)

"""
Send command to stop generation for a channel through com port
"" Parameters : com : com port to use
""              channel : channel for which stop generation
"""
def stop_gen(com: serial.Serial, channel: int):
    # create payload
    payload = [COMMAND_STOP_GEN_VALUE, channel]
    # send payload on USB com
    com.write(payload)

"""
Send command to set generation sampling frequency through com port
"" Parameters : com : com port to use
""              frequency : sampling frequency
"""
def set_gen_freq(com: serial.Serial, freq: float):
    # create payload
    payload = [COMMAND_SET_GEN_FREQ_VALUE, freq]
    # send payload on USB com
    com.write(payload)

"""
Send command to set anti aliasing filter for a channel through com port
"" Parameters : com : com port to use
""              channel : channel for which set filter
""              filter : anti aliasing filter to set
"""
def set_anti_aliasing_filter(com: serial.Serial, channel: int, filter: int):
    # create payload
    payload = [COMMAND_SET_ANTI_ALIA_FILTER, channel | (filter * 16)]
    # send payload on USB com
    com.write(payload)

"""
"" Format samples for sending
"" The input samples are ints on 32 bits. It is converted to 2 ints on 8 bits (little value first). Then the associated
"" output channel command is written on 8 bits too and a padding of 8 bits is added to create a new value on 32 bits
"" Ex : In : 256 which must be sent on the first channel; Out : [0x0, 0x1, 0x1A, 0x0]
"" Parameters : samples : samples to format by input channel
                filters : filter functions for each output channel
""              channels_out : Generation channels usages
"" Returns the formatted data
"""
def build_payload(samples: list[list[int]],
                  filters: list[callable],
                  channels_out: list[bool]) -> list[int]:
    global last_channel_samples
    global single_info_message
    usb_payload: list[int] = []
    channel_samples: list[list[int]] = [[], [], [], []]

    used_channels: list[bool] = []
    max_samples: int = 0
    for i in range(len(channels_out)):
        if channels_out[i]:
            used_channels.append(i)
            channel_samples[i] = filters[i](list(samples[INDEX_CH_IN_1]), list(samples[INDEX_CH_IN_2]))
            if channel_samples[i] == [] and not single_info_message:
                print('Warning : With current acquired data and filters, channel ' + str(i+1)
                      + ' does not have output data')
            elif channel_samples != []:
                # Revert to get last element as first in pop (faster)
                channel_samples[i].reverse()
                max_samples = max(max_samples, len(channel_samples[i]))

    single_info_message = True
    i: int = 0
    while i < max_samples and not is_event_set():
        for idx in used_channels:
            if channel_samples[idx] != []:
                sample: int = channel_samples[idx].pop()
                if sample >= VALUE_OVERFLOW_16_BITS:
                    sample = VALUE_OVERFLOW_16_BITS-1
                elif sample < 0:
                    sample = 0
                last_channel_samples[idx]=sample
            else :
                sample = last_channel_samples[idx]
            usb_payload.append(int(sample) & MAX_8_BITS_VALUE)
            usb_payload.append(int(sample) >> BITS_8 & MAX_8_BITS_VALUE)
            # SPI header
            usb_payload.append(SPI_HEADERS[idx])
            # Padding
            usb_payload.append(PAYLOAD_PADDING)
        i += 1
    return usb_payload

def set_event(status: bool):
    global event_mutex
    if not event_mutex.acquire():
        return
    try:
        global event
        event.set() if status else event.clear()
    except Exception:
        pass
    finally:
        event_mutex.release()

def is_event_set() -> bool:
    global event_mutex
    if not event_mutex.acquire():
        return
    event_set = False
    try:
        global event
        event_set = event.is_set()
    except Exception:
        pass
    finally:
        event_mutex.release()
        return event_set