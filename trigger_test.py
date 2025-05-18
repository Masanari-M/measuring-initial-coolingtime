#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 18:02:34 2024

@author: miyamotomanari
"""

import nidaqmx
from nidaqmx.constants import LineGrouping
import time
import numpy as np
import pylablib as pll
from pylablib.devices import uc480
import os

# import CONTEC
import caio
from lib_CONTEC import usbIO

# シャッターを開くための関数
def open_shutter(task):
    task.write(True)
    print("Shutter opened")

# シャッターを閉じるための関数
def close_shutter(task):
    task.write(False)
    print("Shutter closed")

def main():
    # デジタル出力チャネルの設定
    digital_output_channel = "USB6002-shutter/port0/line1"

    # CONTEC usbIO 初期化
    CONTEC = usbIO()

    # 画像の総数
    num_images = 2
    num_measurements = 10
    delay_times = 10  # in ms
    delay_sec_list = w = np.full(10, 0.001)#np.linspace(0, 0.5, delay_times)

    for dt in delay_sec_list:
        for measurement in range(num_measurements):
            print(f"Starting measurement {measurement + 1}/{num_measurements}")

            with nidaqmx.Task() as task:
                task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
                
                measStartTime = time.time()  # 測定開始時のエポックタイムを取得 t0
                
                open_shutter(task)
                time.sleep(dt)
                
                for i in range(num_images):
                    timeatMeas = time.time()  # カメラへトリガーを送る前の時刻を取得
                    CONTEC.sendTrigger()
                    print(f'{i}')
                    time.sleep(0.1)  # 50 ms
                    elapsedTime = timeatMeas - measStartTime  # t0からの経過時間を計算
                    time.sleep(1)
                # シャッターを閉じる
                close_shutter(task)
                
        # 10秒間のインターバル
        time.sleep(1)

    print('close')

if __name__ == "__main__":
    main()
