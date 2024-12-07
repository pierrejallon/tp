#==============================================================================
# Imports
#==============================================================================
import matplotlib.pyplot as plt
from .consts import *

#==============================================================================
# Constants
#==============================================================================

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

#==============================================================================
# Global variables
#==============================================================================

# Sampling frequency of the signal (in Hertz)
sampling_frequency = 0

# Plot figure
fig = None

# Plot axis
ax = None

# Plot background
bg = None

# Plot channel 1 line
line_1 = None
# Plot channel 2 line
line_2 = None

# Window max duration in seconds
time_window_s = 0

# Plot data (completed in each update)
data = [[], []]

# Plot window size
fig_size = 0

# Previous limit on x-axis
prev_xlim = 0

# Previous limit on y-axis
prev_ylim = 0

#==============================================================================
# Functions
#==============================================================================

"""
"" Initialize plot structure
"" Parameters : sf : Sampling frequency of the signal
""              channels_in : Acquisition channels usages
""              time_window_ms : Time window to show (in miliseconds)
"""
def init_plot(sf: float, channels_in: list[bool], time_window_ms: int):
    global sampling_frequency
    global time_window_s
    global fig
    global ax
    global bg
    global line_1
    global line_2
    global fig_size
    global prev_xlim
    global prev_ylim

    try:
        sampling_frequency = sf
        time_window_s = (time_window_ms/NB_MILISECONDS_IN_1_SECOND)
        fig, ax = plt.subplots()
        ax.set_xlabel('Duration (s)')
        ax.set_ylabel('Voltage (V)')
        ax.set_ylim(V_AXIS_MIN, V_AXIS_MAX)
        ax.set_xlim(0, time_window_s)
        prev_xlim = ax.get_xlim()
        prev_ylim = ax.get_ylim()
        if channels_in[INDEX_CH_IN_1]:
            line_1, = ax.plot([], [], label='Channel 1', animated=True)
            ax.draw_artist(line_1)
        if channels_in[INDEX_CH_IN_2]:
            line_2, = ax.plot([], [], label='Channel 2', animated=True)
            ax.draw_artist(line_2)
        fig_size = fig.get_size_inches()
        ax.legend(loc='upper left', bbox_to_anchor=(-0.15, -0.05), ncol = 2)
        plt.show(block=False)
        plt.pause(0.1)
        bg = fig.canvas.copy_from_bbox(fig.bbox)
        fig.canvas.blit(fig.bbox)
    except Exception:
        pass

"""
"" Update plot lines. Check if fullscreen set or limits changed (zoom or unzoom) to update background
"" Parameters : samples : samples to show
""              increasing_samples_len: True if samples is a list with increasing size containing all acquired samples,
                                        False if samples is a list with only last acquired samples
"""
def update_plot(samples: list[list[int]], increasing_samples_len: bool = True):
    global line_1
    global line_2
    global fig
    global ax
    global bg
    global data
    global fig_size
    global prev_xlim
    global prev_ylim

    try:
        if increasing_samples_len:
            data = list(samples)
        else:
            data[INDEX_CH_IN_1].extend(samples[INDEX_CH_IN_1])
            data[INDEX_CH_IN_2].extend(samples[INDEX_CH_IN_2])
        max_len: int = max(len(data[INDEX_CH_IN_1]), len(data[INDEX_CH_IN_2]))
        data_duration_s: float = max_len/sampling_frequency
        if data_duration_s > time_window_s:
            wanted_samples: int = int(time_window_s*sampling_frequency)
            for i in range(len(samples)):
                data[i] = data[i][-wanted_samples:]
            data_duration_s = time_window_s
        if (fig_size != fig.get_size_inches()).any():
                bg = fig.canvas.copy_from_bbox(fig.bbox)   
                fig_size = fig.get_size_inches()
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        if prev_xlim != xlim or prev_ylim != ylim:
            bg = fig.canvas.copy_from_bbox(fig.bbox)   
            prev_xlim = xlim
            prev_ylim = ylim
        fig.canvas.restore_region(bg)
        if line_1 != None:
            line_1.set_xdata([t/sampling_frequency for t in range(len(data[0]))])
            line_1.set_ydata([(((value / (V_MAX * GAIN) * (VREF_PLUS - VREF_MINUS)) - VREF_MEDIUM) * SIGNAL_COEFF)
                                for value in data[INDEX_CH_IN_1]])
            ax.draw_artist(line_1)
        if line_2 != None:
            line_2.set_xdata([t/sampling_frequency for t in range(len(data[1]))])
            line_2.set_ydata([(((value / (V_MAX * GAIN) * (VREF_PLUS - VREF_MINUS)) - VREF_MEDIUM) * SIGNAL_COEFF)
                                for value in data[INDEX_CH_IN_2]])
            ax.draw_artist(line_2)
        fig.canvas.blit(fig.bbox)
        fig.canvas.flush_events()
    except Exception:
        pass


"""
"" Close plot window
"""
def end_plot():
    try:
        plt.close()
    except Exception:
        pass