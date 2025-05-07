# ========================================================
# Project:  BioFPGAG-G6-python
# File:     header.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================

# ========================================================
# Global Variables Class
#  - Global_Var
# Global_Var Must have the following attributes:
#  - protocol
#  - pattern_label
#  - canvas
#  - status_text_id
#  - display_window
#  - is_stopped
#  - is_paused
# Global_Var is used to store all the global variables
# ========================================================
import re
import os
import time  # 確保有匯入 time 模組
import json
import numpy as np
import time
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from tkinter import ttk
import threading
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
import cv2
from PIL import Image, ImageTk
import base64
import json
import requests
#import obswebsocket
#from obswebsocket import obsws


# RASPBERRY_PI_IP = '100.106.170.105'
RASPBERRY_PI_IP = '192.168.0.168'
RPI_ON = False
AD2_ON = True 
OBS_ON = False
DEVELOP_MODE = True

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    ERROR = '\033[91m' #RED
    STATUS = '\033[96m' #BLUE
    RESET = '\033[0m' #RESET COLOR

from typing import Optional
class Global_Var:
    def __init__(self, root: tk.Tk):
        self.dragdrop_app = None
        self.protocol = None
        self.pattern_label: Optional[tk.Label] = None
        self.canvas: Optional[tk.Canvas] = None
        self.status_text_id: Optional[int] = None
        self.display_window: Optional[tk.Toplevel] = None
        self.is_stopped = True  # 追踪是否停止的變數
        self.is_paused = False  # 新增變數來追蹤是否暫停
        self.is_running = False # 追蹤是否正在運行(包含暫停，不包含preview)
        self.pending_id = ''
        self.pause_sec = 0

        from src.App import DragDropApp
        from src.AD2 import AD2Controller

        # 初始化 AD2 控制器 
        if AD2_ON:
            self.ad2_enable = False
            self.ad2 = AD2Controller() 

        # 啟動主應用程式
        self.dragdrop_app = DragDropApp(root, self)
        self.protocol = self.dragdrop_app.protocol
        self.display_window = self.protocol.dual_display_app.root

        

# def Func_update_pattern_image(pattern: np.ndarray, G_var: Global_Var):
#     # 為每個 pattern 創建一個新的 Image 對象
#     img_size = pattern.shape
#     pattern_image = Image.new("RGB", (img_size[1], img_size[0]))
#     # 定義顏色映射 (低飽和度的顏色)
#     color_map = {
#         1: (100, 149, 237),  # 低飽和度的藍色
#         0: (211, 211, 211)   # 低飽和度的灰色
#     }
#     # 根據 pattern 將顏色填充到圖像
#     for i in range(img_size[0]):
#         for j in range(img_size[1]):
#             pattern_image.putpixel((j, i), color_map[pattern[i, j]])
#     # 調整顯示大小
#     pattern_image = pattern_image.resize((512, 512), Image.NEAREST)
#     img_tk = ImageTk.PhotoImage(image=pattern_image)
#     # 更新圖像顯示
#     G_var.pattern_label.img_tk = img_tk  # 避免被垃圾回收
#     G_var.pattern_label.config(image=img_tk)
def Func_update_pattern_image(pattern: np.ndarray, G_var: Global_Var):
    # 定义格子大小、边框大小和间隙大小
    cell_size = 4  # 每格的像素大小
    border_size = 1  # 框线的大小
    gap_size = 2  # 间隙大小
    bg_color = (240, 240, 240)  # 背景色
    color_map = {
        1: (100, 149, 237),  # 低饱和度的蓝色
        0: (211, 211, 211)   # 低饱和度的灰色
    }

    # 确认输入尺寸是否为 128x128 或 256x256
    if pattern.shape in [(128, 128), (256, 256)]:
        img_size = pattern.shape

        if pattern.shape == (128, 128):
            # 128x128 情况下无间隙
            scaled_size = (
                img_size[0] * (cell_size + border_size),
                img_size[1] * (cell_size + border_size)
            )
            img_array = np.full((scaled_size[1], scaled_size[0], 3), bg_color, dtype=np.uint8)

            for i in range(img_size[0]):
                for j in range(img_size[1]):
                    top_left_x = j * (cell_size + border_size)
                    top_left_y = i * (cell_size + border_size)
                    color = color_map[pattern[i, j]]

                    img_array[
                        top_left_y:top_left_y + cell_size,
                        top_left_x:top_left_x + cell_size
                    ] = color

        elif pattern.shape == (256, 256):
            # 256x256 情况下添加间隙
            split_size = 128
            scaled_size = (
                (img_size[1] + gap_size) * (cell_size + border_size),
                (img_size[0] + gap_size) * (cell_size + border_size)
            )
            img_array = np.full((scaled_size[1], scaled_size[0], 3), bg_color, dtype=np.uint8)

            positions = [
                (0, 0),  # Top-left
                (0, split_size + gap_size),  # Top-right
                (split_size + gap_size, 0),  # Bottom-left
                (split_size + gap_size, split_size + gap_size)  # Bottom-right
            ]

            for idx, (start_row, start_col) in enumerate(positions):
                for i in range(split_size):
                    for j in range(split_size):
                        original_i = idx // 2 * split_size + i
                        original_j = idx % 2 * split_size + j

                        top_left_x = (j + start_col) * (cell_size + border_size)
                        top_left_y = (i + start_row) * (cell_size + border_size)
                        color = color_map[pattern[original_i, original_j]]

                        img_array[
                            top_left_y:top_left_y + cell_size,
                            top_left_x:top_left_x + cell_size
                        ] = color

        # 转换为图像对象
        pattern_image = Image.fromarray(img_array)
         # 根据窗口大小调整图像尺寸
        aspect_ratio = scaled_size[0] / scaled_size[1]
        new_width = 700
        new_height = int(new_width / aspect_ratio)

        pattern_image = pattern_image.resize((new_width, new_height))
    else:
        raise ValueError("Input pattern must be 128x128 or 256x256.")

    # 更新图像显示
    img_tk = ImageTk.PhotoImage(image=pattern_image)
    G_var.pattern_label.img_tk = img_tk  # 避免被垃圾回收
    G_var.pattern_label.config(image=img_tk)





def update_status(G_var: Global_Var, status_text):
    # 使用 canvas.itemconfig 更新状态显示的文字
    G_var.canvas.itemconfig(G_var.status_text_id, text=status_text)

def parse_number(value: str) -> float:
    """Convert numbers with suffixes (e.g., '1M', '2K') into integers."""
    multiplier = {'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'K': 1e3, 'M': 1e6, 'G': 1e9}
    if value[-1] in multiplier:
        return float(eval(value[:-1])) * multiplier[value[-1]]
    return float(eval(value))

def format_number(value: float) -> str:
    if value >= 1e6:
        return f"{round(value/1e6, 8)}M"
    elif value >= 1e3:
        return f"{round(value/1e3, 5)}k"
    else:
        return f"{value}"

    