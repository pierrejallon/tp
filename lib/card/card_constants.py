
#==============================================================================
# Constants
#==============================================================================

# Size of the header of the buffer, containing channel on 32 bits and number of samples on 32 bits
HEADER_SIZE = 8

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

COEFF_POSITIVE = 1

COEFF_NEGATIVE = -1

OFFSET_FIX_VALUE = -764

# Coefficient to convert signal from ADC to DAC
SIGNAL_COEFF = 1.22

# Type of incoming buffer
TYPE_ACK_CONF = 0
TYPE_NOK_CONF = 1
TYPE_CONF_DUMP = 9
TYPE_SAMPLES_CHANN_1 = 10
TYPE_SAMPLES_CHANN_2 = 11

#Bits moving
BITS_7 = 7
BITS_8 = 8
BITS_15 = 15
BITS_16 = 16
BITS_24 = 24

MEDIUM_VALUE_24_BITS = 4194304
VALUE_OVERFLOW_16_BITS = 65536


# Gain of the signal
GAIN = 1
# Max value (in Volt) of the signal
VREF_PLUS = 3
# Min value (in Volt) of the signal
VREF_MINUS = -3
# Medium value (in Volt) of the signal
VREF_MEDIUM = 1.5

# Max y axis value (in Volt)
V_AXIS_MAX = 4.5

# Min y axis value (in Volt)
V_AXIS_MIN = -4.5

# Max input value
V_MAX = 131072 # 2**17

# Coefficient of the signal to plot
SIGNAL_COEFF = 2

################
# Data generation
################
MAX_8_BITS_VALUE = 255
VALUE_0V = 32768

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

# Padding to complete 32-bits int
PAYLOAD_PADDING = 0

FREQUENCIES_FROM_INDEX = [100, 500, 1000.2285, 2001.3723, 10034.4036]
PAYLOAD_LEN_BY_FREQUENCY_FOR_ACQUISITION_GENERATION = 8192
# Coefficient between 8 and 32 bits for data conversion
DATA_CONVERSION_COEFF = 4