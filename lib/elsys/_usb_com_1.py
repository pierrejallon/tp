#==============================================================================
# Imports
#==============================================================================
from ._usb_protocol_from_board import *
from ._usb_com_2 import *
from time import sleep, time
from .consts import *
from ._plot import *
from .file_manipulation import *

#==============================================================================
# Constants
#==============================================================================

# Length of the received buffer according to frequency
PAYLOAD_LENS_BY_FREQUENCY = [64, 256, 512, 1024, 1984]

read_count = 0

#==============================================================================
# Functions
#==============================================================================

"""
"" Init loop duration according to channels used and sampling frequency
"" Parameters : sampling_frequency_index : Index of sampling frequency of the signal (0 to 4)
"" Returns the max time to sleep before new acquisition in seconds
"""
def __get_acquisition_loop_duration(sampling_frequency_index: int) -> float:
    return PAYLOAD_LENS_BY_FREQUENCY[sampling_frequency_index] / FREQUENCIES_FROM_INDEX[sampling_frequency_index]

"""
"" Init acquisition variables
"" Parameters : sampling_frequency_index : Index of sampling frequency of the signal (0 to 4)
""              channels_in : Acquisition channels usages
"" Returns the maximum time to sleep at each acquisition loop in seconds, the length of the payload to acquire
"""
def __acquisition_init(sampling_frequency_index: int, channels_in: list[bool]) -> tuple[float, int]:
    acquisition_loop_duration = __get_acquisition_loop_duration(sampling_frequency_index)
    nb_channels_in: int = 0
    for c in channels_in:
        if c:
            nb_channels_in += 1
    payload_len: int = (PAYLOAD_LENS_BY_FREQUENCY[sampling_frequency_index]
                        + HEADER_SIZE_U32) * (NB_U8_IN_U32 * nb_channels_in)
    return acquisition_loop_duration, payload_len

"""
"" Acquire samples from com port and update plot
"" Parameters : com : com port to use
""              acquisition_loop_duration : max time to sleep before new acquisition in seconds
""              channels_in : Acquisition channels usages
""              payload_len : length of the payload to acquire
""              samples : Buffer to store samples for acquisition only
"""
def __acquisition_loop(com: serial.Serial,
                       acquisition_loop_duration: float,
                       channels_in: list[bool],
                       payload_len: int,
                       samples: list[list[int]]):
    global read_count
    last_samples: list[list[int]] = [[], []]

    if is_payload_present(com, payload_len):
        read_count += 1
        read_start_time: float = time()
        last_samples[INDEX_CH_IN_1], last_samples[INDEX_CH_IN_2] = read_data(com, channels_in, payload_len)
        for i in range(len(samples)):
            samples[i].extend(last_samples[i])
            update_plot(samples)
        read_end_duration: float = time() - read_start_time
        sleep(max(acquisition_loop_duration-read_end_duration, 0))

"""
"" Acquire samples from com port and update plot
"" Parameters : com : com port to use
""              acquisition_loop_duration : max time to sleep before new acquisition in seconds
""              channels_in : Acquisition channels usages
""              payload_len : length of the payload to acquire
""              numeric_filters : filters to apply to the samples for acquisition and generation
""              channels_out : Generation channels usages for acquisition and generation
""              display_plot : True to display the signal, False otherwise
"""
def __asynchronous_acquisition_loop(com: serial.Serial,
                       acquisition_loop_duration: float,
                       channels_in: list[bool],
                       payload_len: int,
                       numeric_filters: list[callable],
                       channels_out: list[bool],
                       display_plot: bool = True):
    last_samples: list[list[int]] = [[], []]
    i: int = 0
    while not is_payload_present(com, payload_len) and i < 100:
        sleep(0.001)
        i += 1
    if is_payload_present(com, payload_len):
        read_start_time: float = time()
        last_samples[INDEX_CH_IN_1], last_samples[INDEX_CH_IN_2] = read_data(com, channels_in, payload_len)
        add_samples_to_fifo(last_samples, channels_out, numeric_filters)
        if display_plot:
            update_plot(last_samples, False)
        read_end_duration: float = time() - read_start_time
        sleep(max(acquisition_loop_duration-read_end_duration - 0.1, 0))

"""
"" Acquire samples from com port, show them in a plot and save them into a file
"" Parameters : com : com port to use
""              sampling_frequency_index : Index of sampling frequency of the signal (0 to 4)
""              channels_in : Acquisition channels usages
""              nb_max_samples : number of samples to get before stopping (no limit if 0)
""              time_windows_ms : Time window for the plot in miliseconds
""              saving_in_file : True to save the acquired signal in a file, False otherwise
"""
def acquisition(com: serial.Serial,
                sampling_frequency_index: int,
                channels_in: list[bool],
                nb_max_samples: int,
                time_window_ms: int,
                saving_in_file: bool):
    plot_initialized: bool = False

    try:
        acquisition_loop_duration, payload_len = __acquisition_init(sampling_frequency_index, channels_in)

        samples: list[list[int]] = [[], []]

        init_plot(FREQUENCIES_FROM_INDEX[sampling_frequency_index], channels_in, time_window_ms)
        plot_initialized = True

        if nb_max_samples > 0:
            print('Acquiring', nb_max_samples, 'samples ...')
            while len(samples[INDEX_CH_IN_1]) < nb_max_samples and len(samples[INDEX_CH_IN_2]) < nb_max_samples:
                __acquisition_loop(com, acquisition_loop_duration, channels_in, payload_len, samples)
            for i in range(len(samples)):
                samples[i] = samples[i][:nb_max_samples]
            print('Samples acquired successfully')
        else:
            print('Launching read data...')
            while not is_event_set():
                __acquisition_loop(com, acquisition_loop_duration, channels_in, payload_len, samples)
    except serial.SerialException:
        print('Unexpected serial error. Stopping acquisition')
        set_com_closed()
    finally:
        if plot_initialized:
            end_plot()
        if saving_in_file and ((len(samples[INDEX_CH_IN_1]) > 0) or (len(samples[INDEX_CH_IN_2]) > 0)):
            write_samples_to_file(samples,
                                  FREQUENCIES_FROM_INDEX[sampling_frequency_index],
                                  channels_in)

"""
"" Acquire samples from com port and fill a fifo buffer to send them with another com port in a separated thread
"" Parameters : com : com port to use
""              sampling_frequency_index : Index of sampling frequency of the signal (0 to 4)
""              channels_in : Acquisition channels usages
""              numeric_filters : filters to apply to the acquired signals for each output channel
""              channels_out : Generation channels usages
""              display_plot : True to display the signal, False otherwise
""              time_windows_ms : Time window for the plot in miliseconds
"""
def asynchronous_acquisition(com: serial.Serial,
                             sampling_frequency_index: int,
                             channels_in: list[bool],
                             numeric_filters: list[callable],
                             channels_out: list[bool],
                             display_plot: bool,
                             time_window_ms: int):
    plot_initialized: bool = False
    try:
        acquisition_loop_duration, payload_len = __acquisition_init(sampling_frequency_index, channels_in)

        print('Launching continous read data...')

        if display_plot:
            init_plot(FREQUENCIES_FROM_INDEX[sampling_frequency_index], channels_in, time_window_ms)
            plot_initialized = True

        while not is_event_set() and is_com_open():
            __asynchronous_acquisition_loop(com, acquisition_loop_duration, channels_in, payload_len, numeric_filters,
                               channels_out, display_plot)
        if not is_com_open():
            print('Unexpected serial error. Stopping acquisition')
    except serial.SerialException:
        print('Unexpected serial error. Stopping acquisition')
        set_com_closed()
    finally:
        if plot_initialized:
            end_plot()
