# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 21:12:24 2024

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
import multiprocessing
import time

# シャッターを開くための関数
def open_shutter(task):
    task.write(True)
    print("Shutter opened")

# シャッターを閉じるための関数
def close_shutter(task):
    task.write(False)
    print("Shutter closed")

def task1(startTime, digital_output_channel, sync_event):
    try:
        print('task1: Waiting for synchronization signal')
        sync_event.wait()  # 同期信号を待機
        print('task1: Opening shutter')
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
            open_shutter(task)
            now1 = time.perf_counter()
            print(f'task1 time: {now1 - startTime}')
    except Exception as e:
        print(f'Error in task1: {e}')

def task2(startTime, sync_event):
    try:
        # CONTEC usbIO 初期化
        CONTEC = usbIO()
        
        print('task2: Waiting for synchronization signal')
        sync_event.wait()  # 同期信号を待機
        print('task2: Sending trigger')
        CONTEC.sendTrigger()
        now2 = time.perf_counter()
        print(f'task2 time: {now2 - startTime}')
    except Exception as e:
        print(f'Error in task2: {e}')

def main():
    print("Starting parallel tasks")
    startTime = time.perf_counter()

    # デジタル出力チャネルの設定
    digital_output_channel = "USB6002-shutter/port0/line1"

    # 同期イベントの作成
    sync_event = multiprocessing.Event()

    # プロセスの作成
    process1 = multiprocessing.Process(target=task1, args=(startTime, digital_output_channel, sync_event))
    process2 = multiprocessing.Process(target=task2, args=(startTime, sync_event))

    # プロセスの開始
    process1.start()
    process2.start()

    # 同期信号を送信（プロセスを同時に開始）
    print('Main process: Sending synchronization signal')
    sync_event.set()

    # プロセスの終了を待機
    process1.join()
    process2.join()

    # シャッターを閉じる
    print("Closing shutter")
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
        close_shutter(task)

    # 10秒間のインターバル
    time.sleep(1)

    print('close')

if __name__ == "__main__":
    main()
