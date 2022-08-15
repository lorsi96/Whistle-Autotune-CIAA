from signal import signal
import numpy as np
from typing import Iterable, Callable
from scipy import signal
# *************************************************************************** #
#                                  Utilities                                  #
# *************************************************************************** #

def generate_music_tones(intervals:Iterable, octaves_n=8) -> np.ndarray:
    """Generates an array with frequencies corresponding to musical tones, 
        starting from C0.

    Args:
        intervals (Iterable): list with the scale's intervals. 
        octaves_n (int, optional): Number of octaves to generate. Defaults to 8.

    Returns:
        np.ndarray: frequencies.
    
    Example:
        # do_maj_scale = generate_music_tones(intervals=[1,1,1,.5,1,1,1,.5])
    """
    A0 = 13.75
    exps = np.cumsum(2 * np.array([0] + intervals)) 
    return np.array(
        [A0*(2**x)*(2**((y+3)/12)) for x in range(octaves_n) for y in exps])


# ********************************* Sythesis ******************************** #

WaveformGenerator = Callable[[float, int], np.ndarray]

def gen_squarewave(fhz:float, samples:int, sr:float=44100) -> np.ndarray:
    n = np.arange(samples)
    sig =  (signal.square(2 * np.pi * fhz * n / sr) + 1) * 128
    return sig 


def gen_waveforms(gen:WaveformGenerator, scale:Iterable, sr_hz:float=44100, 
                  duration_s:float=1) -> Iterable[np.ndarray]:
    """Generate waveforms for a given scale.

    Args:
        gen (WaveformGenerator): waveform generator function.
        scale (Iterable): frequencies of a given scale.

    Returns:
        Iterable[np.ndarray]: List with waveforms generated for each input freq.
    """
    samples = sr_hz * duration_s
    return [gen(f, samples, sr_hz) for f in scale]


# *************************************************************************** #
#                                Actual Tables                                #
# *************************************************************************** #
C_MAJOR_TABLE = [
    16.35,
    18.35,
    20.60,
    21.83,
    24.50,
    27.50,
    30.87,
    32.70,
    36.71,
    41.20,
    43.65,
    49.00,
    55.00,
    61.74,
    65.41,
    73.42,
    82.41,
    87.31,
    98.00,
    110.00, 
    123.47, 
    130.81, 
    146.83, 
    164.81, 
    174.61, 
    196.00, 
    220.00, 
    246.94, 
    261.63, 
    293.66, 
    329.63, 
    349.23, 
    392.00, 
    440.00, 
    493.88, 
    523.25, 
    587.33, 
    659.25, 
    698.46, 
    783.99, 
    880.00, 
    987.77, 
    1046.50,
    1174.66,
    1318.51,
    1396.91,
    1567.98,
    1760.00,
    1975.53,
    2093.00,
    2349.32,
    2637.02,
    2793.83,
    3135.96,
    3520.00,
    3951.07,
    4186.01,
]
