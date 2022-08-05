import time
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa

FILE = "somefile.txt"

class Sample:
    tone: float
    amp: float

    def __init__(self, rawline:str) -> None:
        tone, amp = rawline.split(',')
        self.tone = float(tone)
        self.amp = float(amp)

def smooth_data_convolve_my_average(arr, span):
    re = np.convolve(arr, np.ones(span * 2 + 1) / (span * 2 + 1), mode="same")
    re[0] = np.average(arr[:span])
    for i in range(1, span + 1):
        re[i] = np.average(arr[:i + span])
        re[-i] = np.average(arr[-i - span:])
    return re


with open(FILE, 'rt') as f:
    samples = (Sample(l) for l in f.readlines()) 

music = []
g_last_tone = 0

def gen_tone(f, samples, sr= 8000):
    global g_last_tone
    if samples == 0:
        return []
    if f < 50:
        ff = g_last_tone
    else:
        ff = f
    g_last_tone = ff
    return (np.sin(2 * np.pi * ff / 2 * np.arange(0, samples * 128 / sr, 1/sr))) * (2**15)

last_tone = 0
sample_count = 0

for sample in samples:
    if sample.tone != last_tone:
        music.extend(gen_tone(last_tone, sample_count))
        last_tone = sample.tone
        sample_count = 0
    else:
        sample_count += 1
        
music_filter = smooth_data_convolve_my_average(music, 2)

#plt.plot(music)
#plt.plot(music_filter)
#plt.show()


player = sa.play_buffer(np.array(music).astype(np.int16), 1, 2, 8000)
while player.is_playing():
    time.sleep(1)




