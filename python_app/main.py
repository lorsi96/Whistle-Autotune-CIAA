import pygame as pg
from ciaa_utils import CIAACollector, CIAADataSource
from music_utils import gen_waveforms, gen_squarewave, C_MAJOR_TABLE, print_tone

SAMPLE_WIDTH = 16
FPS = 44100
N_CHANNELS = 2
BUFFER = 1024

if __name__ == '__main__':

    ## Ciaa data collector.
    collector = CIAACollector()
    source = CIAADataSource(collector)

    ## Generate tones to be played.
    tones = gen_waveforms(gen_squarewave, C_MAJOR_TABLE)

    ## Initialize Pygame's mixer.
    pg.mixer.pre_init(FPS, -SAMPLE_WIDTH, N_CHANNELS, BUFFER)
    pg.init()
    sounds = [pg.mixer.Sound(buffer=tne) for tne in tones]

    ## Main Loop: wait for CIAA frequencies and play sounds.
    last = 0
    while True:
        tne = source.wait_for_sample()
        if last != tne and tne != 0:
            sounds[last].fadeout(1)
            sounds[tne].play()
            # print(C_MAJOR_TABLE[tne])
            print_tone(C_MAJOR_TABLE[tne])
            last = tne

