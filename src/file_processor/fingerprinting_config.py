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
# FINGERPRINTS CONFIG:

SAMPLE_RATE = 44100
""" When a file is fingerprinted it is resampled to SAMPLE_RATE Hz.
Higher sample rates mean more accuracy in recognition, but also slower recognition
and larger database file sizes. Setting it higher than the sample rate for your
input files could potentially cause problems.
"""

PEAK_BOX_SIZE = 30
""" The number of points in a spectrogram around a peak for it to be considered a peak.
Setting it higher reduces the number of fingerprints generated but also reduces accuracy.
Setting it too low can severely reduce recognition speed and accuracy.
"""

POINT_EFFICIENCY = 0.5  # default value 0.8
""" A factor between 0 and 1 that determines the number of peaks found for each file.
Affects database size and accuracy.
"""

TARGET_START = 0.05
""" How many seconds after an anchor point to start the target zone for pairing.
See paper for more details.
"""

TARGET_T = 1.8
""" The width of the target zone in seconds. Wider leads to more fingerprints and greater accuracy
to a point, but then begins to lose accuracy.
"""

TARGET_F = 4000
""" The height of the target zone in Hz. Higher means higher accuracy.
Can range from 0 - (0.5 * SAMPLE_RATE).
"""

FFT_WINDOW_SIZE = 0.2
""" The number of seconds of audio to use in each spectrogram segment. Larger windows mean higher
frequency resolution but lower time resolution in the spectrogram.
"""
