# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 20:47:04 2024

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
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# シャッターを開くための関数
def open_shutter(task):
    task.write(True)
    print("Shutter opened")

# シャッターを閉じるための関数
def close_shutter(task):
    task.write(False)
    print("Shutter closed")

def task1(startTime, task):
    try:
        print('task1: Opening shutter')
        open_shutter(task)
        now1 = time.time()
        print(f'task1 time: {now1 - startTime}')
    except Exception as e:
        print(f'Error in task1: {e}')

def task2(startTime, CONTEC):
    try:
        print('task2: Sending trigger')
        CONTEC.sendTrigger()
        now2 = time.time()
        print(f'task2 time: {now2 - startTime}')
    except Exception as e:
        print(f'Error in task2: {e}')

def main():
    print("Starting parallel tasks")
    startTime = time.time()
    
    # CONTEC usbIO 初期化
    CONTEC = usbIO()

    # デジタル出力チャネルの設定
    digital_output_channel = "USB6002-shutter/port0/line1"
    
    # 並列処理の設定
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(task1, startTime, task),
                executor.submit(task2, startTime, CONTEC)
            ]
            for future in as_completed(futures):
                try:
                    future.result()  # 例外が発生した場合はここでキャッチ
                except Exception as e:
                    print(f'Error occurred: {e}')
    
    # シャッターを閉じる
    print("Closing shutter")
    close_shutter(task)

    # 10秒間のインターバル
    time.sleep(10)
    
    print('close')

if __name__ == "__main__":
    main()
