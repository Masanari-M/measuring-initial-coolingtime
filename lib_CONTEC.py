import ctypes
import sys
import caio
import time


class usbIO():
    def __init__(self):
        self.Id = ctypes.c_short()
        self.DeviceName = ctypes.c_char()
        self.DeviceName = "AIO000"
        
        Ret = ctypes.c_long()
        
        Ret.value = caio.AioInit(self.DeviceName.encode(), ctypes.byref(self.Id))
        
    def ON(self):
        Data = ctypes.c_short(int(1))
        ChNo = ctypes.c_short(int(0))
        
        Ret = caio.AioOutputDoBit(self.Id, ChNo, Data)
        
    def OFF(self):
        Data = ctypes.c_short(int(0))
        ChNo = ctypes.c_short(int(0))
        
        Ret = caio.AioOutputDoBit(self.Id, ChNo, Data)
        
    def sendTrigger(self):
        self.ON()
        time.sleep(0.02)
        self.OFF()
        
        
