from enum import Enum, auto
import time
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa

FILE = "somefile.txt"

class State(Enum):
    SILENT = auto()
    PLAYING = auto()

class Sample:
    tone: float
    amp: float

    def __init__(self, rawline:str) -> None:
        tone, amp = rawline.split(',')
        self.tone = float(tone)
        self.amp = float(amp)


state = State(State.SILENT)
samples = []

with open(FILE, 'rt') as f:
    samples = (Sample(l) for l in f.readlines()) 

music = []

def gen_tone(f, samples, sr= 8000):
    if samples == 0:
        return []
    if f < 50:
        return np.zeros(samples * 128)
    return (np.sin(2 * np.pi * f * np.arange(0, samples * 512 / sr, 1/sr))) * (2**15)

last_tone = 0
sample_count = 0

for sample in samples:
    if sample.tone != last_tone:
        music.extend(gen_tone(last_tone, sample_count))
        last_tone = sample.tone
        sample_count = 0
    else:
        sample_count += 1
    
#plt.plot(np.arange(len(music)) * 1/10000, music)
#plt.show()

sig = ((2**15 - 1) * np.sin(2 * np.pi * 440 * np.arange(0, 1, 1/8000))).astype(np.int16)

player = sa.play_buffer(np.array(music).astype(np.int16), 1, 2, 8000)
while player.is_playing():
    time.sleep(1)




