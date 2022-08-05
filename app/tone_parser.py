#!python3
import numpy as np
import sys
import io
import serial
import struct


outfile = "somefile.txt"
sys.stdout = open(outfile, "w")

STREAM_FILE=("/dev/ttyUSB1","serial")
SAMPLING_FREQUENCY_HZ = 8_000 

tone_samps = np.zeros(SAMPLING_FREQUENCY_HZ)
last_f = 0
header = { "head": b"head", "id": 0, "N": 128, "fs": SAMPLING_FREQUENCY_HZ, "maxIndex":0, "maxValue":0,"matchedTone":0.0,"tail":b"tail" }

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

streamFile = serial.Serial(port=STREAM_FILE[0],baudrate=460800,timeout=None)

while True:
    findHeader(streamFile, header)
