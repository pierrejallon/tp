#==============================================================================
# Imports
#==============================================================================
import time
from .consts import *
import serial

#==============================================================================
# Constants
#==============================================================================

# Size of the header of the buffer, containing channel on 32 bits and number of samples on 32 bits
HEADER_SIZE_U8 = 8
HEADER_SIZE_U32 = 2

# Type of incoming buffer
TYPE_ACK_CONF = 0
TYPE_NOK_CONF = 1
TYPE_CONF_DUMP = 9
TYPE_SAMPLES_CHANN_1 = 10
TYPE_SAMPLES_CHANN_2 = 11

# Number of int on 8 bits in a int on 32 bits
NB_U8_IN_U32 = 4

# Index of the data LSB in the buffer
DATA_LSB_INDEX = 2

# Index of the data middle bits in the buffer
DATA_MIDDLE_BITS_INDEX = 1

# Index of the len LSB in the buffer
LEN_LSB_INDEX = 4

# Index of the len first middle bits in the buffer
LEN_MIDDLE_BITS_1_INDEX = 5

# Index of the len second middle bits in the buffer
LEN_MIDDLE_BITS_2_INDEX = 6

# Index of the len MSB in the buffer
LEN_MSB_INDEX = 7

# Positive coefficient if sample value >= average
COEFF_POSITIVE = 1

# Negative coefficient if sample value < average
COEFF_NEGATIVE = -1

# Value to remove to sample to fix offset
OFFSET_FIX_VALUE = -764

# Coefficient to convert signal from ADC to DAC
SIGNAL_COEFF = 1.22

#==============================================================================
# Global variables
#==============================================================================

corrupted_data = False

#==============================================================================
# Functions
#==============================================================================

"""
"" Read data from a com port
"" Parameters : com : com port to use
""              channels_in : Acquisition channels usages
""              payload_len : length of the payload to acquire
"" Returns the samples extracted from the data
"""
def read_data(com: serial.Serial, channels_in: list[bool], payload_len: int) -> tuple[list[int], list[int]]:
    size = com.in_waiting
    rest = size%payload_len
    data: list[int] = com.read(size-rest)
    return compute_data_samples(data, channels_in)

"""
"" Check if data is present in a com port
"" Parameters : com : com port to use
""              payload_len : length of the payload to acquire
"" Returns True if enough data present, False otherwise
"""
def is_payload_present(com: serial.Serial, payload_len: int) -> bool:
    return (com.in_waiting >= payload_len)

"""
"" Extract samples for a channel from a buffer
"" Parameters : data : buffer to treat
""              channels_in : Acquisition channels usages
"" Returns the next index for any data in the buffer, the extracted samples
"""
def extract_samples(data: list[int], channel_in: bool) -> tuple[int, list[int]]:
    samples: list[int] = []
    len_samples: int = data[LEN_LSB_INDEX]
    len_samples += data[LEN_MIDDLE_BITS_1_INDEX] << BITS_8
    len_samples += data[LEN_MIDDLE_BITS_2_INDEX] << BITS_16
    len_samples += data[LEN_MSB_INDEX] << BITS_24
    i: int = 0
    if channel_in:
        for i in range(HEADER_SIZE_U8, len_samples*NB_U8_IN_U32+HEADER_SIZE_U8, NB_U8_IN_U32):
            if i+3 < len(data):
                # uint32
                sample: int = data[i+DATA_LSB_INDEX] + (data[i+DATA_MIDDLE_BITS_INDEX] << BITS_8) + (data[i] << BITS_16)
                coeff: int = COEFF_POSITIVE if sample >= MEDIUM_VALUE_24_BITS else COEFF_NEGATIVE
                diff: int = int((sample - MEDIUM_VALUE_24_BITS)*coeff)
                sample = MEDIUM_VALUE_24_BITS+int(diff*coeff*SIGNAL_COEFF)
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
        i = len_samples*4+HEADER_SIZE_U8
    return i, samples

"""
"" Analyse buffer and get samples for each channel from it
"" Parameters : data : buffer to treat
""              channels_in : Acquisition channels usages
"" Returns the found samples for each channel
"""
def compute_data_samples(data: list[int], channels_in: list[bool]) -> tuple[list[int], list[int]]:
    global corrupted_data

    samples_chann_1: list[int] = []
    samples_chann_2: list[int] = []
    index: int = 0
    channel_in: bool = False
    while (index < len(data)):
        type: int = int(data[index])
        if type == TYPE_ACK_CONF:
            if corrupted_data:
                corrupted_data = False
            time.sleep(NB_MILISECONDS_IN_1_SECOND)
            print("Success: ACK conf")
            break
        elif type == TYPE_NOK_CONF:
            if corrupted_data:
                corrupted_data = False
            print("Error: NACK conf")
            break
        elif type == TYPE_SAMPLES_CHANN_1:
            if corrupted_data:
                corrupted_data = False
            channel_in = channels_in[INDEX_CH_IN_1]
            new_index, samples_chann_1 = extract_samples(data[index:], channel_in)
            index += new_index
        elif type == TYPE_SAMPLES_CHANN_2:
            if corrupted_data:
                corrupted_data = False
            channel_in = channels_in[INDEX_CH_IN_2]
            new_index, samples_chann_2 = extract_samples(data[index:], channel_in)
            index += new_index
        else:
            if not corrupted_data:
                print("Error: Invalid data received. Waiting to retrieve correct data (if it takes a long time, " + \
                    "please stop this program and reset the board) ...")
                corrupted_data = True
            break
    return samples_chann_1, samples_chann_2