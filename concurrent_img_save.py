# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 20:36:25 2024

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
import datetime
import matplotlib.pyplot as plt

exposure_time = 0.001 # in [second]
intervalTime = 10 # in [sec.]

# シャッターを開くための関数
def open_shutter(task):
    task.write(True)

# シャッターを閉じるための関数
def close_shutter(task):
    task.write(False)
    
class Camera():
    def __init__(self):
        self.cam = uc480.UC480Camera()
        self.cam.open()
        self.exposure_time = exposure_time 
        
    def SETTING(self):
        self.cam.set_trigger_mode("ext_rise")
        status = self.cam.get_trigger_mode()
        self.cam.set_exposure(self.exposure_time)
        
        h_start = 770
        h_end = 870
        v_start = 410
        v_end = 480
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
        
def task1(digital_output_channel1, digital_output_channel2):
    try:
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(digital_output_channel1, line_grouping=LineGrouping.CHAN_PER_LINE)
            open_shutter(task)
            
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(digital_output_channel2,line_grouping=LineGrouping.CHAN_PER_LINE)
            open_shutter(task)
            
            # time.sleep(1)
            
    except Exception as e:
        print(f'Error in task1: {e}')

def task2(_hcam, CONTEC, timePath, dt, num_images, measurement):
    try:
        measStartTime = time.time()  # 測定開始時のエポックタイムを取得 t0
        
        for i in range(num_images):
            timeatMeas = time.time()
            CONTEC.sendTrigger()
            img = _hcam.getImage()

            # 経過時間の計算
            elapsedTime = timeatMeas - measStartTime

            # 画像をファイルに保存
            img_filename = os.path.join(timePath, f"img_waittime={int(elapsedTime*1000)}ms-MeasNo{measurement}_img{i}.npy")
            np.save(img_filename, img)
            
            # 経過時間をテキストファイルに保存
            with open(os.path.join(timePath, f"result_waittime={int(dt*1000)}ms-MeasNo{measurement}.txt"), 'a') as f:
                f.write(f"{elapsedTime:.6f}\n")

    except Exception as e:
        print(f'Error in task2: {e}')
        
def main():
    savePath = "C:/Users/triac/Documents/data"

    today = time.time()
    today_dt = datetime.datetime.fromtimestamp(today)
    todayFolderName = today_dt.strftime("%Y-%m-%d")
    todayPath = os.path.join(savePath, todayFolderName)

    if not os.path.isdir(todayPath):
        os.makedirs(todayPath)
    
    timeFolderName = today_dt.strftime("%H-%M-%S")
    timePath = os.path.join(todayPath, timeFolderName)
    
    if not os.path.isdir(timePath):
        os.makedirs(timePath)

    _hcam = Camera()
    _hcam.SETTING()

    # CONTEC usbIO 初期化
    CONTEC = usbIO()

    # デジタル出力チャネルの設定
    digital_output_channel1 = "USB6002-shutter/port0/line1"
    digital_output_channel2 = "USB6002-shutter/port0/line2"
    
    num_images = 40
    num_measurements = 1
    delay_times = 1  # in ms
    delay_sec_list = np.linspace(0, 0.02, delay_times)
    
    for dt in delay_sec_list:
        for measurement in range(num_measurements):
            try:
                # 並列処理の設定
                with ThreadPoolExecutor(max_workers=2) as executor:
                    executor.submit(task1, digital_output_channel1, digital_output_channel2)
                    executor.submit(task2, _hcam, CONTEC, timePath, dt, num_images, measurement)
                    
            finally:
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(digital_output_channel1, line_grouping=LineGrouping.CHAN_PER_LINE)
                    close_shutter(task)                
                    
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(digital_output_channel2, line_grouping=LineGrouping.CHAN_PER_LINE)
                    close_shutter(task)
                    
            time.sleep(intervalTime)
              
    _hcam.CLOSE()                

if __name__ == "__main__":
    main()
