# ========================================================
# Project:  BioFPGAG-G6-python
# File:     Chip.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================

# ========================================================
# Chip Class
#  - send_pattern_to_pi()
#  - read_from_pi()
#  - BIST()
#  - reset_chip_on_pi()
# Chip Class is used to control the chip on Raspberry Pi by HTTP
# Must give the Raspberry Pi IP address as RASPBERRY_PI_IP
# ========================================================

import requests
import numpy as np
import csv
import matplotlib.pyplot as plt
import math

# RASPBERRY_PI_IP = '100.106.170.105'
RASPBERRY_PI_IP = '100.94.43.76'



def preprocess_pattern(pattern):
    cur_x = 0 
    cur_y = 127
    # Declare  numpy binary array as 128x128
    processed_pattern = np.zeros((128*128),  dtype=int)
    for col_num in range(0, 128):
        if col_num % 2 == 1:
            processed_pattern[0 + col_num*128 : 128 + col_num*128] = pattern[:,127-col_num]
        else:
            processed_pattern[0 + col_num*128 : 128 + col_num*128] = pattern[-1::-1,127-col_num]
    # write to csv
    np.savetxt('processed_pattern.csv', processed_pattern, delimiter=',', fmt='%d')
    return processed_pattern

def rebuild_pattern(processed_pattern):
    # Declare  numpy binary array as 128x128
    pattern = np.zeros((128, 128),  dtype=int)
    for col_num in range(0, 128):
        if col_num % 2 == 1:
            pattern[:,127-col_num] = processed_pattern[0 + col_num*128 : 128 + col_num*128]
        else:
            pattern[-1::-1,127-col_num] = processed_pattern[0 + col_num*128 : 128 + col_num*128]
    return pattern


###############################################
# Action 01 - Send Pattern to Raspberry Pi
###############################################
def send_pattern_to_pi(pattern):
    if pattern.shape == (128, 128):
        # 若為 128x128，直接處理並發送
        processed_pattern = preprocess_pattern(pattern)  # 預處理數據
        processed_pattern = processed_pattern.tolist()  # 將 numpy 陣列轉換為列表

        url = f'http://{RASPBERRY_PI_IP}:5000/send_pattern'
        headers = {'Content-Type': 'application/json'}

        data = {"pattern": processed_pattern}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("Pattern processed successfully!")
    elif pattern.shape == (256, 256):
        # 若為 256x256，拆分為四個區塊並處理
        split_size = 128
        pattern_1 = pattern[:split_size, :split_size]  # Top-left
        pattern_2 = pattern[:split_size, split_size:]  # Top-right
        pattern_3 = pattern[split_size:, :split_size]  # Bottom-left
        pattern_4 = pattern[split_size:, split_size:]  # Bottom-right

        # 水平反轉 pattern_2 和 pattern_4
        pattern_2_flipped = np.fliplr(pattern_2)
        pattern_4_flipped = np.fliplr(pattern_4)

        processed_pattern_1 = preprocess_pattern(pattern_1)  # 預處理數據
        processed_pattern_2 = preprocess_pattern(pattern_2_flipped)  # 預處理數據
        processed_pattern_3 = preprocess_pattern(pattern_3)  # 預處理數據
        processed_pattern_4 = preprocess_pattern(pattern_4_flipped)  # 預處理數據

        # 將 numpy 陣列轉換為列表
        processed_pattern_1 = processed_pattern_1.tolist()
        processed_pattern_2 = processed_pattern_2.tolist()
        processed_pattern_3 = processed_pattern_3.tolist()
        processed_pattern_4 = processed_pattern_4.tolist()

        url = f'http://{RASPBERRY_PI_IP}:5000/send_pattern'
        headers = {'Content-Type': 'application/json'}

        data = {
            "pattern_1": processed_pattern_1,
            "pattern_2": processed_pattern_2,
            "pattern_3": processed_pattern_3,
            "pattern_4": processed_pattern_4
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("Pattern processed successfully!")
    else:
        raise ValueError("Input pattern must be 128x128 or 256x256.")

###############################################
# Action 02 - Read Pattern from Raspberry Pi
###############################################
def read_from_pi():
    url = f'http://{RASPBERRY_PI_IP}:5000/read_out_pattern'
    response = requests.get(url)
    if response.status_code == 200:
        print("Pattern read successfully!")
        flattened_pattern_from_chip = response.json().get('pattern_from_chip', [])

        if len(flattened_pattern_from_chip) == 128 * 128:
            # 128x128 pattern
            pattern = rebuild_pattern(flattened_pattern_from_chip)
            return pattern
        elif len(flattened_pattern_from_chip) == 256 * 256:
            # 256x256 pattern, split into four 128x128 blocks
            chunk_size = len(flattened_pattern_from_chip) // 4
            pattern_1 = rebuild_pattern(flattened_pattern_from_chip[0*chunk_size:1*chunk_size])
            pattern_2 = rebuild_pattern(flattened_pattern_from_chip[1*chunk_size:2*chunk_size])
            pattern_3 = rebuild_pattern(flattened_pattern_from_chip[2*chunk_size:3*chunk_size])
            pattern_4 = rebuild_pattern(flattened_pattern_from_chip[3*chunk_size:4*chunk_size])

            # 水平鏡射 pattern_2 和 pattern_4
            pattern_2_flipped = np.fliplr(pattern_2)
            pattern_4_flipped = np.fliplr(pattern_4)

            # 重組為 256x256 pattern
            top_half = np.hstack((pattern_1, pattern_2_flipped))
            bottom_half = np.hstack((pattern_3, pattern_4_flipped))
            full_pattern = np.vstack((top_half, bottom_half))

            return full_pattern
        else:
            raise ValueError("Unexpected pattern size received.")
    else:
        print(f"Error read out pattern: {response.status_code}, {response.text}")
        return None

###############################################
# Action 03 - BIST
###############################################
# 在 Raspberry Pi 上處理 Pattern 並接收結果
def BIST(pattern):
    reset_chip_on_pi()
    send_pattern_to_pi(pattern)
    received_pattern = read_from_pi()
    return received_pattern

###############################################
# Action 04 - Reset Chip
###############################################
def reset_chip_on_pi():
    url = f'http://{RASPBERRY_PI_IP}:5000/reset'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print("Chip reset successfully!")
    else:
        print(f"Error resetting chip: {response.status_code}")


import tkinter as tk
from tkinter import Toplevel
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# 顯示 pattern 的視覺化
def display_patterns_in_gui(original, received, callfunc):
    # Create a new top-level window
    window = Toplevel()
    window.title("Pattern Visualization")

    # Create a figure for plotting
    fig = Figure(figsize=(10, 5), dpi=100)

    # Create subplots
    axs = fig.add_subplot(1, 2, 1)
    axs.imshow(original, cmap='jet')
    axs.set_title('Original Pattern')
    axs.axis('off')

    axs2 = fig.add_subplot(1, 2, 2)
    axs2.imshow(received, cmap='jet')
    axs2.set_title('Pattern From Chip')
    axs2.axis('off')

    # Embed the figure into Tkinter window using FigureCanvasTkAgg
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()

    # Pack the canvas to fill the window
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh(window: tk.Toplevel):
        window.destroy()
        callfunc()

    # Add a refresh button
    refresh_button = tk.Button(window, text="Refresh", command=lambda: refresh(window))
    refresh_button.pack(side=tk.BOTTOM, padx=10, pady=10)

    window.mainloop()


    
