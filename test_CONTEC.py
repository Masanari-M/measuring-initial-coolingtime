import caio 
from lib_CONTEC import usbIO
import time


CONTEC = usbIO()

while True:
    CONTEC.sendTrigger()
    time.sleep(1.0)

    