# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 20:53:28 2024

@author: triac
"""

import nidaqmx
from nidaqmx.constants import LineGrouping
import numpy as np
import pylablib as pll
from pylablib.devices import uc480
import os
import caio
from lib_CONTEC import usbIO
from concurrent.futures import ThreadPoolExecutor
import time
import matplotlib.pyplot as plt

exposure_time = 0.001 # in [second]

# シャッターを開くための関数
def open_shutter(task):
    task.write(True)
    # print("Shutter opened")

# シャッターを閉じるための関数
def close_shutter(task):
    task.write(False)
    # print("Shutter closed")
    
class Camera():
    def __init__(self):
        self.cam = uc480.UC480Camera()
        self.cam.open()
        self.exposure_time = exposure_time 
        
    def SETTING(self):
        self.cam.set_trigger_mode("ext_rise")
        status = self.cam.get_trigger_mode()
        self.cam.set_exposure(self.exposure_time)
        
        h_start = 0
        h_end = 1280
        v_start = 0
        v_end = 1028
        self.cam.set_roi(hstart = h_start
                    ,hend = h_end
                    ,vstart = v_start
                    ,vend = v_end
                    , hbin=1, vbin=1)
                    
        self.cam.start_acquisition(nframes=100)
        
        status = self.cam.get_trigger_mode()
        print(status)
        
        print("get acquire timing", self.cam.get_frame_timings())
        
        print("-- finish setting -- ")
        
    def getImage(self):
        print(self.cam.get_frames_status())
        image = self.cam.read_newest_image()
        
        return image
        
    def CLOSE(self):
        self.cam.stop_acquisition()
        self.cam.close()
        
def task1(digital_output_channel):
    try:
        # print('task1: Opening shutter')
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
            open_shutter(task)
            time.sleep(3)
            close_shutter(task)
    except Exception as e:
        print(f'Error in task1: {e}')

def task2(_hcam, CONTEC):

    try:
        CONTEC.sendTrigger()
        time.sleep(0.001)
    except Exception as e:
        print(f'Error in task2: {e}')

def main():
    
    _hcam = Camera()
    _hcam.SETTING()
    print("Starting parallel tasks")

    # CONTEC usbIO 初期化
    CONTEC = usbIO()

    # デジタル出力チャネルの設定
    digital_output_channel = "USB6002-shutter/port0/line1"
    
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
        close_shutter(task)
        
    try:
    # 並列処理の設定
        with ThreadPoolExecutor(max_workers=2) as executor:
            # futures = [
            executor.submit(task1, digital_output_channel),
            executor.submit(task2, _hcam, CONTEC)
            # ]
            # for future in as_completed(futures):
                # try:
                    # future.result()  # 例外が発生した場合はここでキャッチ
                # except Exception as e:
                    # print(f'Error occurred: {e}')

        with nidaqmx.Task() as task:
                task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
                close_shutter(task)
                

    # シャッターを閉じる
    # print("Closing shutter")
    # この時点でのシャッターの閉じ方を考慮する必要があります。
    # ここでは手動でのシャッター操作は行っていません。
        
    finally:
        
        img = _hcam.getImage()
         
        _hcam.CLOSE()
        
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
            close_shutter(task)
        
        print('close')
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.imshow(img)
        plt.show()

if __name__ == "__main__":
    main()
