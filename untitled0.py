# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 18:02:50 2024

@author: triac
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 15:11:04 2024

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
        
        # roi設定
        ion_pos = [160,350]

        # v_start= ion_pos[1]-50  # min 0
        # v_end =  ion_pos[1]+50 # max 1024
        # h_start= ion_pos[0]-100 # min 0
        # h_end =  ion_pos[0]+100  # max 1280
        # #wx
        v_start= ion_pos[1]-20  # min 0
        v_end =  ion_pos[1]+20 # max 1024
        h_start= ion_pos[0]-40 # min 0
        h_end =  ion_pos[0]+40  # max 1280
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
    Fluorescence_ndarr = []
    elapsedTime_ndarr = []

    try:
        measStartTime = time.time()  # 測定開始時のエポックタイムを取得
        time.sleep(dt)
        for i in range(num_images):
            timeatMeas = time.time()
            CONTEC.sendTrigger()
            img = _hcam.getImage()
            
            if img is None:
                print("Failed to retrieve image from camera.")
                continue  # 画像が取得できなかった場合は次のループへ
            
            elapsedTime = timeatMeas - measStartTime  # t0からの経過時間を計算
            elapsedTime_ndarr.append(elapsedTime)
            Fluorescence_ndarr.append(np.sum(img))

        # ここでの変数変換と保存処理
        elapsedTime_ndarr = np.array(elapsedTime_ndarr)
        Fluorescence_ndarr = np.array(Fluorescence_ndarr)
        output_ndarr = np.stack([elapsedTime_ndarr, Fluorescence_ndarr], axis=1)
        
        print(output_ndarr.dtype)
        np.savetxt(timePath + "/result_waittime=%dms-MeasNo%d.txt" % (dt * 10**6, measurement), output_ndarr)

    except Exception as e:
        print(f'Error in task2: {e}')




def main():
    savePath = "C:/Users/triac/Documents/data"

    today = time.time()
    today_dt = datetime.datetime.fromtimestamp(today)
    todayFolderName = today_dt.strftime("%Y-%m-%d")
    todayPath = savePath + '/' + todayFolderName

    if not os.path.isdir(todayPath):
        os.makedirs(todayPath)
    
    timeFolderName = today_dt.strftime("%H-%M-%S")
    timePath = todayPath + '/' + timeFolderName
    
    if not os.path.isdir(timePath):
        os.makedirs(timePath)

    _hcam = Camera()
    _hcam.SETTING()
    # print("Starting parallel tasks")

    # CONTEC usbIO 初期化
    CONTEC = usbIO()

    # デジタル出力チャネルの設定
    digital_output_channel1 = "USB6002-shutter/port0/line1"
    digital_output_channel2 = "USB6002-shutter/port0/line2"
    
    num_images = 30
    num_measurements = 1
    delay_times = 1# in ms
    delay_sec_list = np.linspace(0, 0.02, delay_times)
    
    for dt in delay_sec_list:
        for measurement in range(num_measurements):
            try:
            # 並列処理の設定
                with ThreadPoolExecutor(max_workers=2) as executor:
                    executor.submit(task1, digital_output_channel1, digital_output_channel2),
                    executor.submit(task2, _hcam, CONTEC, timePath, dt, num_images, measurement)
                
            finally:
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(digital_output_channel1,line_grouping=LineGrouping.CHAN_PER_LINE)
                    close_shutter(task)                
                    
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(digital_output_channel2,line_grouping=LineGrouping.CHAN_PER_LINE)
                    close_shutter(task)
                    
            time.sleep(intervalTime)
              
    _hcam.CLOSE()                

if __name__ == "__main__":
    main()
