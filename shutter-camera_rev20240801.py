#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 18:02:34 2024

@author: miyamotomanari
"""

import nidaqmx
from nidaqmx.constants import LineGrouping
import time
import datetime
import numpy as np
import cv2
import pylablib as pll
from pylablib.devices import uc480
import os

# import CONTEC
import caio
from lib_CONTEC import usbIO



# シャッターを開くための関数
def open_shutter(task):
    task.write(True)  # シャッターを開く
    print("Shutter opened")

# シャッターを閉じるための関数
def close_shutter(task):
    task.write(False)  # シャッターを閉じる
    print("Shutter closed")

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

    try:
        # デジタル出力チャネルの設定
        digital_output_channel = "USB6002-shutter/port0/line1"

        # CONTEC usbIO 初期化
        CONTEC = usbIO()

        # カメラの初期化
        cam = uc480.UC480Camera()
        cam.open()
        cam.set_trigger_mode('ext_rise')
        cam.set_exposure(0.01)  # 最小の露光時間（秒）
        exposure_time = cam.get_exposure()
        print("set exp.time : ", exposure_time)
        
        h_start, h_end = 700, 900
        v_start, v_end = 550, 650
        cam.set_roi(hstart=h_start, hend=h_end, vstart=v_start, vend=v_end, hbin=1, vbin=1)

        # 画像の総数
        num_images = 5
        num_measurements = 1
        delay_times = 10 # in ms
        delay_sec_list = np.linspace(0, 0.5, delay_times)
        
        for dt in delay_sec_list:
            for measurement in range(num_measurements):
                print(f"Starting measurement {measurement + 1}/{num_measurements}")
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
                    
                    #初期化
                    Fluorescence_ndarr = np.array([])
                    elapsedTime_ndarr = np.array([])
                    
                    measStartTime = time.time() # 測定開始時のエポックタイムを取得 t0
                                      
                    open_shutter(task)
                    time.sleep(dt)
                    
                    for i in range(num_images):
                        timeatMeas = time.time() # カメラへトリガーを送る前の時刻を取得
                        CONTEC.sendTrigger()
                        img = cam.snap()  # 画像を読み出し
                        elapsedTime = timeatMeas - measStartTime # t0からの経過時間を計算
                        
                        elapsedTime_ndarr = np.append(elapsedTime_ndarr, elapsedTime)
                        Fluorescence_ndarr = np.append(Fluorescence_ndarr, np.sum(img))
                        
                        
                        # time.sleep(0.03) # 30ms待機 
                      

                    output_ndarr = np.stack([elapsedTime_ndarr, Fluorescence_ndarr], 1)        
                    np.savetxt(timePath + "/result_waittime=%dms-MeasNo%d.txt" %(dt*10**6, measurement), output_ndarr)
                    
                # シャッターを閉じる
                close_shutter(task)
                    
        
        # 10秒間のインターバル
        time.sleep(1)
            
    finally:
        # カメラを閉じる
        print("close")
        cam.close()
        cv2.destroyAllWindows()
        
    
    

if __name__ == "__main__":
    main()