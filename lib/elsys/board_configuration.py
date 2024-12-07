#==============================================================================
# Imports
#==============================================================================
from ._usb_com_1 import *
from ._usb_protocol_to_board import *
from ._usb_com_2 import *
from threading import Thread
import serial
from time import sleep
from .enums import *
import signal

#==============================================================================
# Constants
#==============================================================================

# Baud rate of the COM ports
COM_PORT_BAUDRATE = 2000000

# Timeout of the COM ports
COM_PORT_TIMEOUT = 0.04

# Buffer size of the COM ports
COM_PORT_BUFFER_SIZE = 65536

#==============================================================================
# Functions
#==============================================================================

def signal_handler(_sig, _frame):
    print('Interruption signal caught ! Initiating program end')
    set_event(True)

"""
"" Launch threads to do acquisition and generation simultaneously
"" Parameters : com_1 : First port com to use
""              com_2 : Second port com to use
""              sampling_frequency_index : Index of sampling frequency of the signal (0, 1 or 2)
""              channels_in : Acquisition channels usages
""              channels_out : Generation channels usages
""              filters : filters to apply to the acquired signals for each output channel
"" Returns the list of the created threads
"""
def __start_generation_thread(com_2: str,
                               sampling_frequency_index: int,
                               channels_out: list[bool]) -> Thread:
    print('Starting generation thread')
    gen_thread: Thread = Thread(target = asynchronous_generation,
                        args=(com_2, sampling_frequency_index, channels_out))
    gen_thread.start()
    print('Generation thread started successfully')
    return gen_thread

"""
"" Check program parameters validity and fix them if necessary
"" Parameters : com_1 : First port com to use
""              com_2 : Second port com to use
""              sampling_frequency_index : Index of sampling frequency of the signal (0, 1 or 2)
""              channels_in : Acquisition channels usages
""              channels_out : Generation channels usages
""              filters : filters to apply to the acquired signals for each output channel
"" Returns 0 if everything is OK, 1 otherwise
"""
def __check_program_parameters(port_1: str,
                                       port_2: str,
                                       sampling_frequency_index: int,
                                       current_mode: int,
                                       channels_in: list[bool],
                                       anti_aliasing_filters: int,
                                       nb_samples: int,
                                       time_window_ms: int,
                                       channels_out: list[bool],
                                       generation_file_name: str) -> int:
    if port_1 == '':
        print('Error : No name defined for first COM port')
        return 1
    if port_2 == '':
        print('Error : No name defined for second COM port')
        return 1
    if sampling_frequency_index < FREQUENCY_100HZ or sampling_frequency_index > FREQUENCY_10KHZ:
        print('Error : Invalid frequency defined')
        return 1
    if current_mode < MODE_ACQUISITION or current_mode > MODE_ACQUISITION_GENERATION:
        print('Error : Invalid mode defined')
        return 1
    at_least_one_channel_in_active: bool = False
    for c in channels_in:
        if c and not at_least_one_channel_in_active:
            at_least_one_channel_in_active = True
    if current_mode != MODE_GENERATION and not at_least_one_channel_in_active:
        print('Error : No input channel to activate')
        return 1
    for i in range(len(anti_aliasing_filters)):
        aaf: int = anti_aliasing_filters[i]
        if aaf < FILTER_50HZ or aaf > NO_FILTER:
            print('Error : Invalid filter defined for input channel', i+1)
            return 1
    if current_mode == MODE_ACQUISITION and nb_samples == 0:
        print('Warning : No number of samples defined. Acquisition will continue until you stop it with Ctrl + C')
    if current_mode == MODE_ACQUISITION and time_window_ms == 0:
        print('Error : No time window defined')
        return 1
    at_least_one_channel_out_active: bool = False
    for c in channels_out:
        if c and not at_least_one_channel_out_active:
            at_least_one_channel_out_active = True
    if current_mode != MODE_ACQUISITION and not at_least_one_channel_out_active:
        print('Error : No output channel to activate')
        return 1
    if current_mode == MODE_GENERATION and generation_file_name == '':
        print('Error : No file name defined for generation source')
        return 1
    return 0

"""
"" Main program
"" Parameters : port_1 : Name of the first port COM of the board
""              port_2 : Name of the second port COM of the board
""              sampling_frequency : Sampling frequency of the signal (in Hertz)
""              current_mode : Mode of the board (acquisition, generation or both)
""              channels_in : Acquisition channels usages
""              filter : Filter used for acquisition
""              nb_samples : Number of samples to acquire
""              channels_out : Generation channels usages
""              generation_file_name : Name of the file to read samples from
"" Returns 0 if everything is OK, 1 otherwise
"""
def board_config(port_1: str,
                 port_2: str,
                 sampling_frequency_index: int,
                 current_mode: int,
                 channels_in: list[bool] = [False, False],
                 anti_aliasing_filters: list[int] = [NO_FILTER, NO_FILTER],
                 nb_samples: int = 0,
                 time_window_ms: int = 0,
                 channels_out: list[bool] = [False, False, False, False],
                 generation_file_name: str = '',
                 numeric_filters: list[callable] = [],
                 saving_in_file: bool = False,
                 display_plot: bool = False) -> int:
    check_result = __check_program_parameters(port_1,
                                              port_2,
                                              sampling_frequency_index,
                                              current_mode,
                                              channels_in,
                                              anti_aliasing_filters,
                                              nb_samples,
                                              time_window_ms,
                                              channels_out, generation_file_name)

    if check_result != 0:
        return check_result

    print('Starting program')

    signal.signal(signal.SIGINT, signal_handler)

    com_1 = serial.Serial()
    com_2 = serial.Serial()

    print('Opening ports')
    com_1.port = port_1
    com_1.baudrate=COM_PORT_BAUDRATE
    com_1.timeout = COM_PORT_TIMEOUT
    com_1.set_buffer_size(rx_size = COM_PORT_BUFFER_SIZE, tx_size = COM_PORT_BUFFER_SIZE)
    try:
        com_1.open()
    except serial.SerialException as e:
        print('Impossible to open port', port_1)
        return 1
    print('Port', port_1, 'opened !')

    com_2.port = port_2
    com_2.baudrate=COM_PORT_BAUDRATE
    com_2.timeout = COM_PORT_TIMEOUT
    com_2.set_buffer_size(rx_size = COM_PORT_BUFFER_SIZE, tx_size = COM_PORT_BUFFER_SIZE)
    try:
        com_2.open()
    except serial.SerialException as e:
        print('Impossible to open port', port_2)
        return 1
    print('Port', port_2, 'opened !')

    print('Configuring board')
    reset_board(com_1)

    if current_mode != MODE_GENERATION:
        for i in range(len(channels_in)):
            if channels_in[i]:
                print('Activating input port', i+1)
                start_acquire(com_1, i)
                set_anti_aliasing_filter(com_1, i, anti_aliasing_filters[i])
            else:
                print('Deactivating input port', i+1)
                stop_acquire(com_1, i)
        set_acquire_freq(com_1, sampling_frequency_index)
    else:
        for i in range(len(channels_in)):
            print('Deactivating input port', i+1)
            stop_acquire(com_1, i)

    if current_mode != MODE_ACQUISITION:
        for i in range(len(channels_out)):
            if channels_out[i]:
                print('Activating output port', i+1)
                start_gen(com_1, i)
            else:
                print('Deactivating output port', i+1)
                stop_gen(com_1, i)
        set_gen_freq(com_1, sampling_frequency_index)
    else:
        for i in range(len(channels_out)):
            print('Deactivating output port', i+1)
            stop_gen(com_1, i)

    print('Configuration complete !')

    set_event(False)

    if current_mode == MODE_ACQUISITION:
        acquisition(com_1, sampling_frequency_index, channels_in, nb_samples, time_window_ms, saving_in_file)
    elif current_mode ==  MODE_GENERATION:
        generation(com_2, generation_file_name, sampling_frequency_index, channels_out, numeric_filters)
    elif current_mode == MODE_ACQUISITION_GENERATION:
        gen_thread: Thread = __start_generation_thread(com_2, sampling_frequency_index, channels_out)
        asynchronous_acquisition(com_1, sampling_frequency_index, channels_in, numeric_filters, channels_out,
                                 display_plot, time_window_ms)
        print('Checking generation thread stopped')
        while (gen_thread.is_alive()):
            sleep(0.1)
        print('Generation thread stopped')
    else:
        print('Invalid mode', current_mode, '!')

    print('Deactivating board')
    if current_mode != MODE_GENERATION and is_com_open():
        for i in range(len(channels_in)):
            if channels_in[i]:
                print('Deactivating input port', i+1)
                stop_acquire(com_1, i)
    if current_mode != MODE_ACQUISITION and is_com_open():
        for i in range(len(channels_out)):
            if channels_out[i]:
                print('Deactivating output port', i+1)
                stop_gen(com_1, i)

    if is_com_open():
        com_2.close()
        com_1.close()

    print('Board deactivated')
    return 0
