#!python3
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from   matplotlib.animation import FuncAnimation
import os
import sys
import io
import serial
import struct
import simpleaudio as sa

outfile = "somefile.txt"
sys.stdout = open(outfile, "w")

STREAM_FILE=("/dev/ttyUSB1","serial")
#STREAM_FILE=("log.bin","file")


tone_samps = np.zeros(8000)
last_f = 0
player: Optional[sa.PlayObject] = None
header = { "head": b"head", "id": 0, "N": 128, "fs": 8000, "maxIndex":0, "maxValue":0,"matchedTone":0.0,"tail":b"tail" }
fig    = plt.figure ( 1 )

adcAxe = fig.add_subplot ( 2,1,1                            )
adcLn, = plt.plot        ( [],[],'r-',linewidth=4           )
adcAxe.grid              ( True                             )
adcAxe.set_ylim          ( -2 ,2                            )


fftAxe      = fig.add_subplot ( 2,1,2                                 )
fftLn,      = plt.plot        ( [],[],'b-',linewidth = 5,alpha  = 1   )
ciaaFftLn,  = plt.plot        ( [],[],'r-',linewidth = 10,alpha = 0.4 )
maxValueLn, = plt.plot        ( [],[],'y-',linewidth = 2,alpha  = 0.3 )
maxIndexLn, = plt.plot        ( [],[],'y-o',linewidth = 6,alpha = 0.8 )
fftAxe.grid                   ( True                                  )
fftAxe.set_ylim               ( 0 ,0.25                               )

def findHeader(f,h):
    find=False
    while(not find):
        data=bytearray(len(h["head"]))
        while data!=h["head"]:
            data+=f.read(1)
            data[:]=data[-4:]

        h["id"]       = readInt4File(f,4)
        h["N" ]       = readInt4File(f)
        h["fs"]       = readInt4File(f)
        h["maxIndex"] = readInt4File(f,4)
        h["maxValue"] = (readInt4File(f,sign = True)*1.65**2)/(2**4*512) #el resultado sale en 3.13 y yo arranque con 1.15 corrido 6 a la izq. asi que ahora solo basta correr 4 a la derecha, normalizar con 1.65/512, pero como lo muestro comparando con potencia, elevo al cuadrado
        h["matchedTone"] = readFloat4File(f)
        data=bytearray(b'1234')
        for i in range(4):
            data+=f.read(1)
            data[:]=data[-4:]
        find = data==h["tail"]

    print(f'{h["matchedTone"]},{h["maxValue"]}')
    return h["id"],h["N"],h["fs"],h["maxIndex"],h["maxValue"],h["matchedTone"]

def readInt4File(f,size=2,sign=False):
    raw=f.read(1)
    while( len(raw) < size):
        raw+=f.read(1)
    return (int.from_bytes(raw,"little",signed=sign))

def readFloat4File(f,size=4):
    raw=f.read(1)
    while( len(raw) < size):
        raw+=f.read(1)
    return struct.unpack('<f',raw)[0]

def flushStream(f,h):
    if(STREAM_FILE[1]=="serial"): #pregunto si estoy usando la bibioteca pyserial o un file
        f.flushInput()
    else:
        f.seek ( 2*h["N"],io.SEEK_END)

def readSamples(adc,fft,N,trigger=False,th=0):
    state="waitLow" if trigger else "sampling"
    i=0
    for t in range(N):
        sample = (readInt4File(streamFile,sign = True)*1.65)/(2**6*512)
        #part real plus imag
        fftBin = (readInt4File(streamFile,sign = True)*1.65)/(2**6*512) +\
                 1j*(readInt4File(streamFile,sign = True)*1.65)/(2**6*512)
        state,nextI= {
                "waitLow" : lambda sample,i: ("waitHigh",0) if sample<th else ("waitLow" ,0),
                "waitHigh": lambda sample,i: ("sampling",0) if sample>th else ("waitHigh",0),
                "sampling": lambda sample,i: ("sampling",i+1)
                }[state](sample,i)
        adc[i]=sample
        fft[i]=fftBin
        i=nextI

def update(t):
    global header
    global tone_samps
    global player
    global last_f
    flushStream ( streamFile,header )
    id,N,fs,maxIndex,maxValue,matchedTone=findHeader ( streamFile,header )
    adc     = np.zeros(N)
    ciaaFft = np.zeros(N).astype(complex)
    time    = np.arange(0,N/fs,1/fs)
    readSamples(adc,ciaaFft,N,False,0)

    if matchedTone > 200:
        if last_f == matchedTone and player.is_playing():
            pass
        else:
            tone_samps = (2**15-1) * maxValue / 0.2 * np.sin(2 * np.pi * matchedTone * np.arange(0, 10, 1/8000)) 
            #if player is not None and player.is_playing():
            #    player.stop()
            #player = sa.play_buffer(tone_samps.astype(np.int16), 1, 2, 8000)

    adcAxe.set_xlim ( 0    ,N/fs )
    adcLn.set_data  ( time ,adc  )

    fft=np.abs ( 1/N*np.fft.fft(adc ))**2
    fftAxe.set_ylim ( 0 ,np.max(fft)+0.006)
    fftAxe.set_xlim ( 0 ,fs/2 )
    fftLn.set_data    ( (fs/N )*fs*time ,fft)
    ciaaFftLn.set_data ( (fs/N )*fs*time ,np.abs(ciaaFft)**2)

    maxValueLn.set_data ( time,maxValue           )
    maxIndexLn.set_data ( [(fs/N )*fs*time[maxIndex],(fs/N )*fs*time[maxIndex]],[0,maxValue] )

    return adcLn, fftLn,  maxValueLn,  maxIndexLn, ciaaFftLn

#seleccionar si usar la biblioteca pyserial o leer desde un archivo log.bin
if(STREAM_FILE[1]=="serial"):
    streamFile = serial.Serial(port=STREAM_FILE[0],baudrate=460800,timeout=None)
else:
    streamFile=open(STREAM_FILE[0],"rb",0)

ani=FuncAnimation(fig,update,8000,init_func=None,blit=True,interval=1,repeat=True)
plt.draw()
plt.get_current_fig_manager().window.showMaximized() #para QT5
plt.show()
streamFile.close()
