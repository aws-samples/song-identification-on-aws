"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import numpy as np
import av
from av import AudioResampler
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter
from fingerprinting_config import SAMPLE_RATE, PEAK_BOX_SIZE, POINT_EFFICIENCY, \
    TARGET_START, TARGET_T, TARGET_F, FFT_WINDOW_SIZE


def get_fingerprints(filename):
    f, t, Sxx = file_to_spectrogram(filename)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)
    hashes = hash_points(peaks)
    hashes = sorted(hashes, key=lambda x: x[1])
    return hashes


def file_to_spectrogram(filename):
    """Calculates the spectrogram of a file.

    Converts a file to mono and resamples to :data:`~abracadabra.SAMPLE_RATE` before
    calculating. Uses :data:`~abracadabra.FFT_WINDOW_SIZE` for the window size.

    :param filename: Path to the file to spectrogram.
    :returns: * f - list of frequencies
              * t - list of times
              * Sxx - Power value for each time/frequency pair
    """
    audio = get_samples_from_file(filename)
    nperseg = int(SAMPLE_RATE * FFT_WINDOW_SIZE)
    return spectrogram(audio, SAMPLE_RATE, nperseg=nperseg)


def find_peaks(Sxx):
    """Finds peaks in a spectrogram.

    Uses :data:`~abracadabra.PEAK_BOX_SIZE` as the size of the region around each
    peak. Calculates number of peaks to return based on how many peaks could theoretically
    fit in the spectrogram and the :data:`~abracadabra.POINT_EFFICIENCY`.

    Inspired by
    `photutils
    <https://photutils.readthedocs.io/en/stable/_modules/photutils/detection/core.html#find_peaks>`_.

    :param Sxx: The spectrogram.
    :returns: A list of peaks in the spectrogram.
    """
    data_max = maximum_filter(Sxx, size=PEAK_BOX_SIZE, mode='constant', cval=0.0)
    peak_goodmask = (Sxx == data_max)  # good pixels are True
    y_peaks, x_peaks = peak_goodmask.nonzero()
    peak_values = Sxx[y_peaks, x_peaks]
    i = peak_values.argsort()[::-1]
    # get co-ordinates into arr
    j = [(y_peaks[idx], x_peaks[idx]) for idx in i]
    total = Sxx.shape[0] * Sxx.shape[1]
    # in a square with a perfectly spaced grid, we could fit area / PEAK_BOX_SIZE^2 points
    # use point efficiency to reduce this, since it won't be perfectly spaced
    # accuracy vs speed tradeoff
    peak_target = int((total / (PEAK_BOX_SIZE**2)) * POINT_EFFICIENCY)
    return j[:peak_target]


def idxs_to_tf_pairs(idxs, t, f):
    """Helper function to convert time/frequency indices into values."""
    return np.array([(f[i[0]], t[i[1]]) for i in idxs])


def hash_point_pair(p1, p2):
    """Helper function to generate a hash from two time/frequency points."""
    return hash((p1[0], p2[0], p2[1]-p2[1]))


def target_zone(anchor, points, width, height, t):
    """Generates a target zone as described in `the Shazam paper
    <https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf>`_.

    Given an anchor point, yields all points within a box that starts `t` seconds after the point,
    and has width `width` and height `height`.

    :param anchor: The anchor point
    :param points: The list of points to search
    :param width: The width of the target zone
    :param height: The height of the target zone
    :param t: How many seconds after the anchor point the target zone should start
    :returns: Yields all points within the target zone.
    """
    x_min = anchor[1] + t
    x_max = x_min + width
    y_min = anchor[0] - (height*0.5)
    y_max = y_min + height
    for point in points:
        if point[0] < y_min or point[0] > y_max:
            continue
        if point[1] < x_min or point[1] > x_max:
            continue
        yield point


def hash_points(points):
    """Generates all hashes for a list of peaks.

    Iterates through the peaks, generating a hash for each peak within that peak's target zone.

    :param points: The list of peaks.
    :param filename: The filename of the song, used for generating song_id.
    :returns: A list of tuples of the form (hash, time offset, song_id).
    """
    hashes = []
    for anchor in points:
        for target in target_zone(
            anchor, points, TARGET_T, TARGET_F, TARGET_START
        ):
            hashes.append((
                # hash
                hash_point_pair(anchor, target),
                # time offset
                anchor[1]
            ))
    return hashes


def get_samples_from_file(fname):

    container = av.open(fname)
    audio_stream = next(s for s in container.streams if s.type == 'audio')

    # reset to the start of the file
    container.seek(0, any_frame=False, stream=audio_stream)
    data_stream = container.decode(audio_stream)

    # seek to the start
    frame = next(data_stream)
    if frame is None:
        raise Exception('Cannot get audio frames')

    samples = []
    resampler = AudioResampler(layout="mono", rate=SAMPLE_RATE)

    try:
        while frame:
            # force to 44100, mono
            frame = resampler.resample(frame)[0]

            # then extract samples
            data = frame.to_ndarray()
            samples.append(data[0])

            frame = next(data_stream)
    except ValueError:
        # mp3s sometimes have bad data - ignore those errors
        pass
    except StopIteration:
        pass
    except Exception as e:
        err_type = str(type(e))
        print(f'Exception during extracting audio: {err_type}')

    data_stream.close()

    samples = np.concatenate(samples)
    # convert the samples from 32-bit floats (from -1 to 1)
    # to 16-bit signed integers (from -32768 to 32767)
    if samples.dtype == np.float32:
        samples *= 32767
        samples = samples.astype(np.int16)

    return samples
