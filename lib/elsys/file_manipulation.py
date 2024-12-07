import os
from datetime import datetime

"""
"" Open a file in the filesystem to read its content
"" Parameters : file_name : Name of the file to open
"" Returnns the file if opening is successfull, None otherwise
"""
def open_file_for_reading(file_name: str):
    file = None
    try:
        if not os.path.exists('data'):
            print('Error during opening file data/' + file_name + ' : No data repository in project')
            return file
        file = open('data/' + file_name)
    except OSError:
        print('Impossible to open file data/' + file_name)
    finally:
        return file

"""
"" Open a file in the filesystem or create it to overwrite its content
"" Parameters : file_name : Name of the file to open
"" Returnns the file if opening is successfull, None otherwise
"""
def open_file_for_writing(file_name: str):
    file = None
    try:
        if not os.path.exists('data'):
            os.mkdir('data')
        file = open('data/' + file_name, 'w')
    except OSError:
        print('Impossible to create file data/' + file_name)
    finally:
        return file

"""
"" Write acquisition data into a file
"" the file format is the following :
"" frequency=100|1000|10000
"" channel 1 active=True|False
"" channel 2 active=True|False
"" for each channel a list of sampling with the format <timestamp>:<value> separated by comma. Samples for the next
"" channel are on a new line
"" Parameters : samples : Samples to write in file
""              sampling_frequency : Sampling frequency of the signal (in Hertz)
""              channels_in : Acquisition channels usages
"""
def write_samples_to_file(samples: list[list[int]], sampling_frequency: float, channels_in: list[bool]):
    file_name: str = 'samples_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
    print('Saving samples to data/' + file_name + ' file')
    file = open_file_for_writing(file_name)
    if file == None:
        print('Error during opening of data/' + file_name + ' file. Samples not saved')
        return
    file.write('frequency=' + str(sampling_frequency) + '\n')
    for i in range(len(channels_in)):
        file.write('channel ' + str(i+1) + ' active=' + str(channels_in[i]) + '\n')
    period: float = 1/sampling_frequency
    for i in range(len(samples)):
        if channels_in[i]:
            samples_for_channel: list[int] = samples[i]
            timestamp: float = 0
            for s in samples_for_channel:
                file.write('{:.4f}'.format(timestamp) + ':' + str(s) + ',')
                timestamp += period
            file.write('\n')
    file.close()
    print('Samples saved correctly')

"""
"" Get the list of samples for each input channel from a file
"" The expected file format is the following :
"" frequency=100|1000|10000
"" channel 1 active=True|False
"" channel 2 active=True|False
"" for each channel a list of sampling with the format <timestamp>:<value> separated by comma. Samples for the next
"" channel are on a new line
"" Parameters : file : File to get the samples from
"" Returnns the sampling frequency stored in the file, the input channels using stored in the file, the samples for
"" each input channel stored in the file
"""
def read_samples_from_file(file_name: str):
    frequency: float = -1
    channels_in: list[bool] = []
    samples: list[list[int]] = []

    print('Getting samples from file data/' + file_name)
    file = open_file_for_reading(file_name)
    if file == None:
        print('Error during opening of data/' + file_name + ' file. Stopping generation')
        return frequency, channels_in, samples
    frequency_line = file.readline()
    frequency_line = frequency_line.rstrip()
    frequency_line_split = frequency_line.split('=')
    if len(frequency_line_split) != 2:
        print('Invalid frequency line', frequency_line, '; aborting')
        return frequency, channels_in, samples
    frequency = float(frequency_line_split[1])

    for i in range(2):
        channel_line = file.readline()
        channel_line = channel_line.rstrip()
        channel_line_split = channel_line.split('=')
        if len(channel_line_split) != 2:
            print('Invalid channel', str(i+1), 'line', channel_line, '; aborting')
            return frequency, channels_in, samples
        channel_line_split
        channel_active = True if channel_line_split[1] == 'True' else False
        channels_in.append(channel_active)

    for i in range(len(channels_in)):
        samples.append([])
        if channels_in[i]:
            samples_line = file.readline()
            samples_line = samples_line.rstrip()
            channel_samples = []
            samples_line_split = samples_line.split(',')
            for s in samples_line_split:
                sample_split = s.split(':')
                if len(sample_split) == 2:
                    channel_samples.append(int(sample_split[1]))
            samples[i] = channel_samples
    file.close()
    print('Samples retrieved correctly')
    return frequency, samples
