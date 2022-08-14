from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping
from scipy import signal
import pygame as pg
import time

import numpy as np

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



## Scales Generation ##
def generate_music_tones(intervals:Iterable) -> np.ndarray:  # From C0 to C6
    A0 = 13.75
    exps = np.cumsum(2 * np.array([0] + intervals)) 
    return np.array([A0*(2**x)*(2**((y+3)/12)) for x in range(8) for y in exps])

# do_scale = generate_music_tones(intervals=[1,1,1,.5,1,1,1,.5])

## Tone Generators ##
ToneGenerator = Callable[[float, int], np.ndarray]

def gen_squarewave(fhz:float, samples:int, sr:float=44100) -> np.ndarray:
    n = np.arange(samples)
    sig =  (signal.square(2 * np.pi * fhz * n / sr) + 1) * 128
    return sig  # np.blackman(len(n)) * sig

## Tone Table ##
def gen_tone_table(gen:ToneGenerator, scale:np.ndarray):
    return [gen(f, 441000) for f in scale]



## Tone Provider ##
def melody_gen():
    yield 40
    yield 42
    yield 42
    yield 44
    yield 44

gen = melody_gen()

def get_tone():
    time.sleep(.5)
    try:
        return next(gen)
    except Exception:
        return None


import numpy as np
import serial
import struct

@dataclass
class CIAACollector:
    port: str = '/dev/ttyUSB1'
    baudrate: float = 460_800
    sampling_f_hz: float = 8_000

    def __post_init__(self):
        self.stream = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=None
        )
        self.h = {
            "head": b"head", 
            "id": 0, 
            "N": 128, 
            "fs": self.sampling_f_hz, 
            "maxIndex":0, 
            "maxValue":0,
            "matchedTone":0.0,
            "toneIndex":0,
            "tail":b"tail" 
        }

    def wait_for_data(self) -> Mapping[str, Any]:
        header_found = False
        while not header_found:
            data = bytearray(len(self.h["head"]))
            while data!=self.h["head"]:
                data+= self.stream.read(1)
                data[:] = data[-4:]
                    
            self.h["id"]       = self.readInt4File(self.stream, 4)
            self.h["N" ]       = self.readInt4File(self.stream)
            self.h["fs"]       = self.readInt4File(self.stream)
            self.h["maxIndex"] = self.readInt4File(self.stream, 4)
            self.h["maxValue"] = (self.readInt4File(self.stream, sign = True)*1.65**2)/(2**4*512)
            self.h["matchedTone"] = self.readFloat4File(self.stream)
            self.h["toneIndex"] = self.readInt4File(self.stream, 4)

            
            data=bytearray(b'1234')
            for _ in range(4):
                data+=self.stream.read(1)
                data[:]=data[-4:]
            header_found = data == self.h["tail"]
        return self.h
    
    
    @staticmethod
    def readInt4File(f:serial.Serial, size=2, sign=False):
        raw=f.read(1)
        while( len(raw) < size):
            raw+=f.read(1)
        return (int.from_bytes(raw,"little",signed=sign))

    @staticmethod
    def readFloat4File(f:serial.Serial, size=4):
        raw=f.read(1)
        while( len(raw) < size):
            raw+=f.read(1)
        return struct.unpack('<f',raw)[0]


class CIAADataSource:
    def __init__(self, collector:CIAACollector) -> None:
        self.ciaa = collector
        self.last_index = 0
    
    def wait_for_sample(self) -> int:
        mp = self.ciaa.wait_for_data()
        if mp["maxValue"] >= 0.00:
            self.last_index = mp["toneIndex"]
            return mp["toneIndex"]
        else:
            return self.last_index



if __name__ == '__main__':
    ## Pygame App ##

    SAMPLE_WIDTH = 16
    FPS = 44100
    N_CHANNELS = 2
    BUFFER = 1024

    tones = gen_tone_table(gen_squarewave, C_MAJOR_TABLE)

    pg.mixer.pre_init(44100, -SAMPLE_WIDTH, N_CHANNELS, BUFFER)
    pg.init()
    sounds = [pg.mixer.Sound(buffer=tne) for tne in tones]

    collector = CIAACollector()
    source = CIAADataSource(collector)

    # while True:
    #     ind = source.wait_for_sample()
    #     print(ind)
        

    last = 0
    while True:
        tne = source.wait_for_sample()
        if last != tne and tne != 0:
            sounds[last].stop()
            sounds[tne].play()
            last = tne

