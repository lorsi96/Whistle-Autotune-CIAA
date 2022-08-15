from dataclasses import dataclass
from typing import Any, Mapping
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
