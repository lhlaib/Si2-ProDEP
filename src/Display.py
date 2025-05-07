# ========================================================
# Project:  BioFPGAG-G6-python
# File:     Display.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================

##########################################################################
# How to start the detecting server
# run command
# docker run -it --rm -p 9001:9001 roboflow/roboflow-inference-server-cpu
# on particle_detect(conda env) in 140.113.225.169 (si2 lab server)
# to start the server for object detection

#************************************************************************#
#*****************************important notice***************************#
# MUST ^C twice to stop the server when finish the code
# otherwise the server will never stop
# it could jam the port 9001 and the new server cannot be deploy
#************************************************************************#
#************************************************************************#

# make sure the port is thesame!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##########################################################################

from src.header import *
from PIL import Image, ImageTk
import cv2
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import cv2
import math
from collections import deque
import csv
import os
import glob

class particles:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
class pair:
    def __init__(self, x1, y1, x2, y2, id):
        self.start = (x1, y1)
        self.dest = (x2, y2)
        self.id = id
        
class PathPlanner:
    def __init__(self, map_data, move_pair_list , thickness, hollow):
        self.map = map_data  # 128x128 map where 0 represents free space, other values represent obstacles
        self.move_pair_list = move_pair_list  # dictionary with index as key, containing start, dest, and id
        self.paths = {}  # stores the planned paths for each pair
        self.thickness = thickness
        self.hollow = hollow
        
    def plan_paths(self):
        active_pairs = {pair_id: {'pair': pair, 'current': pair.start, 'path': [pair.start]} for pair_id, pair in self.move_pair_list.items()}
        
        while active_pairs:
            next_positions = {}
            to_remove = []
            for pair_id, data in active_pairs.items():
                pair = data['pair']
                current_position = data['current']
                path = data['path']

                next_step = self.get_next_step(current_position, pair.dest)
                if next_step:
                    next_positions[pair_id] = {'next_step': next_step, 'path': path + [next_step]}
                else:
                    print(f"No valid move found for pair id: {pair.id}")
                    to_remove.append(pair_id)

            # Check for collisions and update positions
            occupied_positions = set()
            for pair_id, data in next_positions.items():
                next_step = data['next_step']
                if self.is_collision_free(next_step, occupied_positions):
                    occupied_positions.add(next_step)
                    active_pairs[pair_id]['current'] = next_step
                    active_pairs[pair_id]['path'] = data['path']
                else:
                    print(f"Collision detected for pair id: {pair_id} at position {next_step}")
                    to_remove.append(pair_id)

            # Remove pairs that have reached the destination or encountered issues
            for pair_id in to_remove:
                if pair_id in active_pairs:
                    del active_pairs[pair_id]

            # Mark paths that have reached the destination
            for pair_id, data in list(active_pairs.items()):
                if data['current'] == data['pair'].dest:
                    self.paths[pair_id] = data['path']
                    self.mark_path_as_obstacle(data['path'])
                    del active_pairs[pair_id]

        return self.paths

    def get_next_step(self, current, dest):
        # Use a simple heuristic to move towards the destination
        x, y = current
        dx = np.sign(dest[0] - x)
        dy = np.sign(dest[1] - y)

        possible_moves = [(x + dx, y), (x, y + dy), (x + dx, y + dy), (x - dx, y), (x, y - dy)]
        for nx, ny in possible_moves:
            if self.is_valid_move(nx, ny):
                return (nx, ny)
        return None

    def is_valid_move(self, x, y):
        # Check if the position is within bounds
        if not (0 <= x < 128 and 0 <= y < 128):
            return False

        # Check if the position is a free space in the map
        if self.map[y][x] != 0:
            return False

        # Check the 5x5 surrounding area for obstacles to avoid particle collision
        for dx in range(self.hollow+self.thickness, self.hollow+self.hollow+1):
            for dy in range(self.hollow+self.thickness, self.hollow+self.hollow+1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 128 and 0 <= ny < 128 and self.map[ny][nx] != 0:
                    return False

        return True

    def is_collision_free(self, position, occupied_positions):
        # Check if the position is not already occupied by another particle in this time step
        return position not in occupied_positions

    def mark_path_as_obstacle(self, path):
        # Mark the planned path on the map to avoid overlap between paths
        for (x, y) in path:
            self.map[y][x] = 1  # Mark as obstacle

# in path
# 0 : nothing
# 1 : target
# 2 : target center
# -1 : obsticle
# -2 : obsticle center
# 3 : destnation 
# 4 : destnation center
# -3 : air wall

class DualDisplayApp:
    def __init__(self, G_var: Global_Var):
        
        self.root = tk.Toplevel() 
        self.root.title("Dual Display with OBS and Pattern Series")
        # G_var.display_window = self.root 

        # 主視窗
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 建立菜單欄
        self.create_menu(G_var)

        # 左邊部分 - DEP Pattern Frame
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.dep_title_label = tk.Label(self.left_frame, text="DEP Pattern", font=("Helvetica", 14, "bold"))
        self.dep_title_label.pack()

        self.pattern_label = tk.Label(self.left_frame)
        self.pattern_label.pack()

        G_var.pattern_label = self.pattern_label  # 將 pattern_label 存入 G_var

        # 右邊部分 - OBS 畫面 Frame
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        self.obs_title_label = tk.Label(self.right_frame, text="Optical Image", font=("Helvetica", 14, "bold"))
        self.obs_title_label.pack()

        self.video_label = tk.Label(self.right_frame)
        self.video_label.pack()

        # 初始化 128x128 的 pattern
        Func_update_pattern_image(np.zeros((128, 128), dtype=bool), G_var)  # 更新左邊顯示的 pattern
        
        # for AI global parameters
        self.ROBOFLOW_API_KEY = "goBS6I0u1Ap5OGdAK3LR"
        self.ROBOFLOW_MODEL = "particle_dect_v2/2" # eg xx-xxxx--#
        self.ROBOFLOW_SIZE = 800
        
        # camara adjust
        self.img = None
        self.cam_x = 0
        self.cam_y = 0
        self.cam_width = 800 #do not change when not necessery
        self.cam_height = 800 #do not change when not necessery
        
        # for calibration
        self.show_cross  = True
        self.top_left_cross_x = 0
        self.top_left_cross_y = 0
        self.bottom_right_cross_x = 800
        self.bottom_right_cross_y = 800
        
        # for detection
        self.confidence = 0.5
        self.overlap = 0.5
        self.detected = False
        self.show_detect = False       
        self.response_json = None
        self.predictions = None
        self.particle_list = {}
        
        # for overlapping
        self.overlapping = False
        
        # for pettern gen
        self.thickness = 3
        self.hollow = 2
        self.pattern = np.zeros((128, 128), dtype=int)
        self.map = np.zeros((128, 128), dtype=int)
        self.set_pattern_mode = 0
        self.show_add_sub = False
        self.max_id = 0
        self.add_sub_pos_x = 0
        self.add_sub_pos_y = 0
        
        # for moving cell
        self.set_position_mode_active = 0
        self.target_select = False
        self.merge_target = False
        self.show_path = False
        self.number = 1
        self.number2 = 0
        self.start_x = 0
        self.start_y = 0
        self.dest_x = 0
        self.dest_y = 0
        #self.merge_x = 0
        #self.merge_y = 0
        self.move_pair_list = {}
        self.path = {}
        self.start_move = False
        self.route_index = 0

        # 啟動 OBS WebSocket 連接
        if OBS_ON:
            self.start_obs_stream()
            self.update_fram(G_var)

    def start_obs_stream(self):
        # 啟動一個新執行緒來檢查 OBS 狀態，避免主執行緒被阻塞
        #threading.Thread(target=self.connect_to_obs, daemon=True).start()
        self.cap = cv2.VideoCapture(2)  # 預設使用第一個Webcam
        # set 1920x1080
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
    def update_fram(self, G_var):
        if self.overlapping:
            self.show_grid(G_var)
        else:
            # 顯示攝影機畫面
            self.show_camera_frame(G_var)

        # 每隔20毫秒更新一次影像
        self.root.after(20, lambda: self.update_fram(G_var))

    def show_grid(self, G_var):
        # 創建128x128網格圖像
        grid_image = Image.new('RGB', (128, 128), color='white')
        draw = ImageDraw.Draw(grid_image)
        
        # in path
        # 0 : nothing
        # 1 : target
        # 2 : target center
        # -1 : obsticle
        # -2 : obsticle center
        # 3 : destnation 
        # 4 : destnation center
        # -3 : air wall

        # 根據 self.map 中的值來填充顏色
        for i in range(128):
            for j in range(128):
                value = self.map[i, j]
                if  value == 4 or value == 3:
                    color = (255, 0, 0)  # 紅色
                elif value == -2 or value == -1 or value == 8:
                    color = (128, 128, 128)  # 灰色
                elif value == 1:
                    color = (0, 0, 255)  # 藍色
                elif value == 2:
                    color = (255, 0, 0)  # 紅色
                elif value == 5:
                    color = (255, 255, 0)
                else:
                    color = (255, 255, 255)  # 白色

                draw.rectangle([j, i, j+1, i+1], fill=color)

        # 將 128x128 的圖像放大顯示
        grid_image = grid_image.resize((512, 512), Image.NEAREST)

        # 將網格轉換為 NumPy 陣列
        grid_np = np.array(grid_image)

        # 讀取攝影機畫面
        ret, frame = self.cap.read()
        if ret:
            frame = frame[self.cam_y:self.cam_y+self.cam_height, self.cam_x:self.cam_x+self.cam_width]
            frame = frame[self.top_left_cross_y:self.bottom_right_cross_y, self.top_left_cross_x:self.bottom_right_cross_x]

            # 將攝影機畫面轉為RGB格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 調整攝影機畫面大小
            frame = cv2.resize(frame, (512, 512))

            # 將攝影機畫面疊加到網格上，使用透明度
            alpha = 0.5  # 透明度值（0.0 - 1.0）
            blended_frame = cv2.addWeighted(frame, alpha, grid_np, 1 - alpha, 0)

            # 將 NumPy 陣列轉換為 PIL 圖片
            blended_image = Image.fromarray(blended_frame)

            # 將 PIL 圖片轉換為 Tkinter 可顯示的格式
            imgtk = ImageTk.PhotoImage(image=blended_image)

            # 更新 Tkinter 的 Label 來顯示影像
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def show_camera_frame(self, G_var):
        # 讀取攝影機畫面  
        ret, frame = self.cap.read()
        if ret:
            # cv2的影像是BGR格式，需要轉換成RGB格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            frame = frame[self.cam_y:self.cam_y+self.cam_height, self.cam_x:self.cam_x+self.cam_width]
            self.img = frame
            
            if self.show_cross:
                size = 20
                color=(0, 0, 255)
                thickness=2
                cv2.line(frame, (self.top_left_cross_x - size, self.top_left_cross_y), (self.top_left_cross_x + size, self.top_left_cross_y), color, thickness)
                cv2.line(frame, (self.top_left_cross_x, self.top_left_cross_y - size), (self.top_left_cross_x,self.top_left_cross_y + size), color, thickness)
                
                cv2.line(frame, (self.bottom_right_cross_x - size, self.bottom_right_cross_y), (self.bottom_right_cross_x + size, self.bottom_right_cross_y), color, thickness)
                cv2.line(frame, (self.bottom_right_cross_x, self.bottom_right_cross_y - size), (self.bottom_right_cross_x,self.bottom_right_cross_y + size), color, thickness)
                
            if self.show_detect and self.response_json != None:
                #predictions = response_json["predictions"]    
                for pred in self.predictions:
                        # get the boundary and confidence
                        x, y, w, h, number = pred["x"], pred["y"], pred["width"], pred["height"], pred["particle_id"]
                        confidence = pred["confidence"]

                        # int of boundary
                        x1, y1 = int(x - w / 2), int(y - h / 2)
                        x2, y2 = int(x + w / 2), int(y + h / 2)
                        # wrong type
                        # x1, y1 = int(x), int(y)
                        # x2, y2 = int(x+w), int(y+h)

                        # draw the frame
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # draw confidence
                        label = f"No.{number},{confidence:.2f}"
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
            
            display_size = (512, 512)  # 根據您的需求調整顯示大小
            resized_frame = cv2.resize(frame, display_size)
            
            # 將影像轉換為PIL的Image格式
            image = Image.fromarray(resized_frame)
            
            # 將PIL影像轉換為ImageTk格式，讓Tkinter可以顯示
            imgtk = ImageTk.PhotoImage(image=image)
            
            
            # 更新Tkinter的Label來顯示影像
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    
    def create_menu(self, G_var):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        cam_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Claibration", menu=cam_menu)
        cam_menu.add_command(label="Adjust Camera", command=lambda: self.open_adjust_camera_window())
        cam_menu.add_separator()
        cam_menu.add_command(label="Set Boundary", command= lambda: self.open_set_bound_window())
        
        AI_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Detection", menu=AI_menu)
        AI_menu.add_command(label="Set Parameter", command=lambda: self.open_set_parameter_window(G_var))
        AI_menu.add_separator()
        AI_menu.add_command(label="Detect Once", command= lambda: self.detect_once(G_var))
        AI_menu.add_command(label="Show/Hide detect", command= lambda: self.detect_change())
        
        pattern_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Generate", menu=pattern_menu)
        pattern_menu.add_command(label="Generate Pattern", command=lambda: self.generate_pattern_window(G_var))
        pattern_menu.add_command(label="Show/Hide Pattern", command=lambda: self.change_overlapping())
        pattern_menu.add_command(label="Add pattern", command= lambda: self.add_pattern())
        pattern_menu.add_command(label="Remove pattern", command= lambda: self.remove_pattern())
        pattern_menu.add_separator()
        pattern_menu.add_command(label="Set Single Movement", command=lambda: self.set_position_mode())
        pattern_menu.add_command(label="Set Two Merge", command=lambda: self.set_two_merge())
        pattern_menu.add_command(label="Start Movement", command=lambda: self.move_cell_window(G_var))
        

    def open_adjust_camera_window(self):
        adjust_window = tk.Toplevel(self.root)
        adjust_window.title("Adjust Camera")

        # Labels and Entry widgets for direct input
        tk.Label(adjust_window, text="Camera X:").grid(row=0, column=0)
        self.x_entry = tk.Entry(adjust_window)
        self.x_entry.grid(row=0, column=1)
        self.x_entry.insert(0, self.cam_x)

        tk.Label(adjust_window, text="Camera Y:").grid(row=1, column=0)
        self.y_entry = tk.Entry(adjust_window)
        self.y_entry.grid(row=1, column=1)
        self.y_entry.insert(0, self.cam_y)

        tk.Label(adjust_window, text="Camera Width:").grid(row=2, column=0)
        self.width_entry = tk.Entry(adjust_window)
        self.width_entry.grid(row=2, column=1)
        self.width_entry.insert(0, self.cam_width)

        tk.Label(adjust_window, text="Camera Height:").grid(row=3, column=0)
        self.height_entry = tk.Entry(adjust_window)
        self.height_entry.grid(row=3, column=1)
        self.height_entry.insert(0, self.cam_height)

        # Button to apply changes
        tk.Button(adjust_window, text="Apply", command=lambda : self.apply_camera_changes()).grid(row=4, columnspan=2)

        # Bind arrow keys for adjustment
        adjust_window.bind("<Left>", self.adjust_left)
        adjust_window.bind("<Right>", self.adjust_right)
        adjust_window.bind("<Up>", self.adjust_up)
        adjust_window.bind("<Down>", self.adjust_down)

    def apply_camera_changes(self):
        try:
            self.cam_x = int(self.x_entry.get())
            self.cam_y = int(self.y_entry.get())
            self.cam_width = int(self.width_entry.get())
            self.cam_height = int(self.height_entry.get())
        except ValueError:
            print("Please enter valid numbers.")

    # Functions for arrow key adjustment
    def adjust_left(self, event):
        if self.cam_x-10 > 0:
            self.cam_x -= 10
        else:
            self.cam_x = 0
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, self.cam_x)

    def adjust_right(self, event):
        if self.cam_x+10 <= 1920:
            self.cam_x += 10
        else:
            self.cam_x = 1920
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, self.cam_x)

    def adjust_up(self, event):
        if self.cam_y-10 > 0 :
            self.cam_y -= 10
        else:
            self.cam_y = 0
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, self.cam_y)

    def adjust_down(self, event):
        if self.cam_y+10 <= 1080:
            self.cam_y += 10
        else:
            self.cam_y = 1080
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, self.cam_y)
        
    def open_set_bound_window(self):
        adjust_window = tk.Toplevel(self.root)
        adjust_window.title("Adjust Boundaries")

        # Top Left X
        tk.Label(adjust_window, text="Top Left X:").grid(row=0, column=0)
        self.x1_entry = tk.Entry(adjust_window)
        self.x1_entry.grid(row=0, column=1)
        self.x1_entry.insert(0, self.top_left_cross_x)
        self.x1_entry.bind("<KeyPress>", lambda event: self.update_variable('top_left_cross_x', self.x1_entry))

        # Top Left X 增加/減少按鈕
        tk.Button(adjust_window, text="▲", command=lambda: self.increment('top_left_cross_x', self.x1_entry, 1)).grid(row=0, column=2)
        tk.Button(adjust_window, text="▼", command=lambda: self.increment('top_left_cross_x', self.x1_entry, -1)).grid(row=0, column=3)

        # Top Left Y
        tk.Label(adjust_window, text="Top Left Y:").grid(row=1, column=0)
        self.y1_entry = tk.Entry(adjust_window)
        self.y1_entry.grid(row=1, column=1)
        self.y1_entry.insert(0, self.top_left_cross_y)
        self.y1_entry.bind("<KeyRelease>", lambda event: self.update_variable('top_left_cross_y', self.y1_entry))

        tk.Button(adjust_window, text="▲", command=lambda: self.increment('top_left_cross_y', self.y1_entry, 1)).grid(row=1, column=2)
        tk.Button(adjust_window, text="▼", command=lambda: self.increment('top_left_cross_y', self.y1_entry, -1)).grid(row=1, column=3)

        # Bottom Right X
        tk.Label(adjust_window, text="Bottom Right X:").grid(row=2, column=0)
        self.x2_entry = tk.Entry(adjust_window)
        self.x2_entry.grid(row=2, column=1)
        self.x2_entry.insert(0, self.bottom_right_cross_x)
        self.x2_entry.bind("<KeyRelease>", lambda event: self.update_variable('bottom_right_cross_x', self.x2_entry))

        tk.Button(adjust_window, text="▲", command=lambda: self.increment('bottom_right_cross_x', self.x2_entry, 1)).grid(row=2, column=2)
        tk.Button(adjust_window, text="▼", command=lambda: self.increment('bottom_right_cross_x', self.x2_entry, -1)).grid(row=2, column=3)

        # Bottom Right Y
        tk.Label(adjust_window, text="Bottom Right Y:").grid(row=3, column=0)
        self.y2_entry = tk.Entry(adjust_window)
        self.y2_entry.grid(row=3, column=1)
        self.y2_entry.insert(0, self.bottom_right_cross_y)
        self.y2_entry.bind("<KeyRelease>", lambda event: self.update_variable('bottom_right_cross_y', self.y2_entry))

        tk.Button(adjust_window, text="▲", command=lambda: self.increment('bottom_right_cross_y', self.y2_entry, 1)).grid(row=3, column=2)
        tk.Button(adjust_window, text="▼", command=lambda: self.increment('bottom_right_cross_y', self.y2_entry, -1)).grid(row=3, column=3)

        

    def update_variable(self, var_name, entry):
        try:
            value = int(entry.get())
            setattr(self, var_name, value)
        except ValueError:
            pass  # 非整數輸入時保持當前值不變

    def increment(self, var_name, entry, delta):
        value = getattr(self, var_name, 0) + delta
        setattr(self, var_name, value)
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def open_set_parameter_window(self, G_var):
        adjust_window = tk.Toplevel(self.root)
        adjust_window.title("Set Detection Parameter")

        # Labels and Entry widgets for direct input
        tk.Label(adjust_window, text="confidence:").grid(row=0, column=0)
        self.confidence_entry = tk.Entry(adjust_window)
        self.confidence_entry.grid(row=0, column=1)
        self.confidence_entry.insert(0, self.confidence)

        tk.Label(adjust_window, text="overlap:").grid(row=1, column=0)
        self.overlap_entry = tk.Entry(adjust_window)
        self.overlap_entry.grid(row=1, column=1)
        self.overlap_entry.insert(0, self.overlap)


        # Button to apply changes
        tk.Button(adjust_window, text="Apply", command=lambda : self.apply_detect_changes(G_var)).grid(row=2, columnspan=2)

    def apply_detect_changes(self, G_var):
        try:
            self.confidence = float(self.confidence_entry.get())
            self.overlap = float(self.overlap_entry.get())
            self.infer_and_render(self.img, G_var)
            self.show_detect = True
        except ValueError:
            print("Please enter valid numbers.")
            
    def detect_once(self, G_var):
        self.infer_and_render(self.img, G_var)
        self.show_detect = True
    
    def infer_and_render(self, cropped_img, G_var):
        #global response_json
        #global detect_get
        # Resize image to match the expected input size of the model
        height, width, channels = cropped_img.shape
        scale = self.ROBOFLOW_SIZE / max(height, width)
        resized_img = cv2.resize(cropped_img, (round(scale * width), round(scale * height)))

        # Encode image to base64 string
        retval, buffer = cv2.imencode('.jpg', resized_img)
        img_str = base64.b64encode(buffer)

        # Prepare the API request
        upload_url = "".join([
            #"https://detect.roboflow.com/",
            #"http://140.113.225.169:9487/",
            "http://ee32.si2.iee.nycu.edu.tw:9001/",
            self.ROBOFLOW_MODEL,
            "?api_key=",
            self.ROBOFLOW_API_KEY,
            "&format=json",
            "&stroke=5"
        ])
        upload_url += f"&confidence={self.confidence}&overlap={self.overlap}"

        # Send request to Roboflow API
        response = requests.post(upload_url, data=img_str, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        #global predictions
        if response.status_code == 200 and response.content:
            try:
                #image = np.asarray(bytearray(response.content), dtype="uint8")
                #image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                self.response_json = response.json()  # update
                self.predictions = self.response_json["predictions"]
                self.detected = True
                self.particle_list.clear()
                for i, prediction in enumerate(self.predictions, start=1):
                    prediction["particle_id"] = i
                    x = prediction["x"]
                    y = prediction["y"]
                    x_center, y_center = int((x-self.top_left_cross_x)/(self.bottom_right_cross_x - self.top_left_cross_x)*128), int((y-self.top_left_cross_y)/(self.bottom_right_cross_y - self.top_left_cross_y)*128)
                    self.particle_list[i] = particles(x_center, y_center)
                    self.max_id = i
                    
                for id, particle in self.particle_list.items():
                    print(f"{id}: {particle.x}, {particle.y}")
                #predictions = response.json()["predictions"]
                # 指定要儲存 JSON 的檔案名稱
                #file_name = "data.json"

                # 開啟檔案以寫入模式
                #with open(file_name, "w") as json_file:
                    # 使用 json.dump() 函數將數據寫入檔案
                    #json.dump(response_json, json_file)
                

                # for pred in predictions:
                #     # get the boundary and confidence
                #     x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
                #     confidence = pred["confidence"]

                #     # int of boundary
                #     x1, y1 = int(x - w / 2), int(y - h / 2)
                #     x2, y2 = int(x + w / 2), int(y + h / 2)

                #     # draw the frame
                #     cv2.rectangle(resized_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

                #     # draw confidence
                #     label = f"{confidence:.2f}"
                #     cv2.putText(resized_img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                return resized_img
            except json.JSONDecodeError:
                print("cannot decode JSON")
                return resized_img
        else:
            print("Error in API request:", response.status_code)
            return resized_img  # return
        
    def detect_change(self):
        self.show_detect = not self.show_detect
        
    def generate_pattern_window(self, G_var):
        adjust_window = tk.Toplevel(self.root)
        adjust_window.title("Set Pattern Parameter")

        # Labels and Entry widgets for direct input
        tk.Label(adjust_window, text="thickness:").grid(row=0, column=0)
        self.thickness_entry = tk.Entry(adjust_window)
        self.thickness_entry.grid(row=0, column=1)
        self.thickness_entry.insert(0, self.thickness)

        tk.Label(adjust_window, text="hollow:").grid(row=1, column=0)
        self.hollow_entry = tk.Entry(adjust_window)
        self.hollow_entry.grid(row=1, column=1)
        self.hollow_entry.insert(0, self.hollow)


        # Button to apply changes
        tk.Button(adjust_window, text="Apply", command=lambda : self.apply_pattern_changes(G_var)).grid(row=2, columnspan=2)

    def apply_pattern_changes(self, G_var):
        try:
            self.thickness = int(self.thickness_entry.get())
            self.hollow = int(self.hollow_entry.get())
            self.generate_pattern()
            Func_update_pattern_image(self.pattern, G_var)
            self.overlapping = True
        except ValueError:
            print("Please enter valid numbers.")
            
    def generate_pattern(self):
        # reset all pattern
        self.pattern[:, :] = 0
        self.map[:, :] = 0
        
        for id, partilce in self.particle_list.items():
            #x, y, w, h , id= pred["x"], pred["y"], pred["width"], pred["height"], pred["particle_id"]
            x_center = partilce.x
            y_center = partilce.y
            #x_center, y_center = int((partilce.x-self.top_left_cross_x)/(self.bottom_right_cross_x - self.top_left_cross_x)*128), int((y-self.top_left_cross_y)/(self.bottom_right_cross_y - self.top_left_cross_y)*128)
            if x_center > 128 or y_center > 128:
                continue
            # 計算擴大後的粒子周圍座標範圍
            
            y_start_hidden, y_end_hidden = max(y_center - (self.hollow+(self.thickness+self.hollow)), 0), min(y_center + (self.hollow+(self.thickness+self.hollow)+1), self.pattern.shape[0])
            x_start_hidden, x_end_hidden = max(x_center - (self.hollow+(self.thickness+self.hollow)), 0), min(x_center + (self.hollow+(self.thickness+self.hollow)+1), self.pattern.shape[1])
            
            for y in range(y_start_hidden, y_end_hidden):
                for x in range(x_start_hidden, x_end_hidden):
                    #pattern[x, y] = 1
                    if self.merge_target and id == self.number2:
                        self.map[y, x] = 0
                    elif self.target_select and id == self.number:
                        self.map[y, x] = 0
                    else:
                        self.map[y, x] = -3
                    #self.map[y, x] = 0 if self.target_select and id == self.number else -3
            
                    
        for id, partilce in self.particle_list.items():
            #x, y, w, h , id= pred["x"], pred["y"], pred["width"], pred["height"], pred["particle_id"]
            #x_center, y_center = int((x-self.top_left_cross_x)/(self.bottom_right_cross_x - self.top_left_cross_x)*128), int((y-self.top_left_cross_y)/(self.bottom_right_cross_y - self.top_left_cross_y)*128)
            x_center = partilce.x
            y_center = partilce.y
            if x_center > 128 or y_center > 128:
                continue
            # 計算擴大後的粒子周圍座標範圍
            y_start, y_end = max(y_center - (self.thickness+self.hollow), 0), min(y_center + (self.thickness+self.hollow) + 1, self.pattern.shape[0])
            x_start, x_end = max(x_center - (self.thickness+self.hollow), 0), min(x_center + (self.thickness+self.hollow) + 1, self.pattern.shape[1])
            
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    self.pattern[y, x] = 1
                    self.map[y, x] = 1 if self.target_select and id == self.number else -1
                
                
        for id, partilce in self.particle_list.items():
            #x, y, w, h , id= pred["x"], pred["y"], pred["width"], pred["height"], pred["particle_id"]
            #x_center, y_center = int((x-self.top_left_cross_x)/(self.bottom_right_cross_x - self.top_left_cross_x)*128), int((y-self.top_left_cross_y)/(self.bottom_right_cross_y - self.top_left_cross_y)*128)
            x_center = partilce.x
            y_center = partilce.y
            if x_center > 128 or y_center > 128:
                continue
            # 計算擴大後的粒子周圍座標範圍
            
            y_start_hollow, y_end_hollow = max(y_center - self.hollow, 0), min(y_center + self.hollow + 1, self.pattern.shape[0])
            x_start_hollow, x_end_hollow = max(x_center - self.hollow, 0), min(x_center + self.hollow + 1, self.pattern.shape[1])
            
                
            for y in range(y_start_hollow, y_end_hollow):
                for x in range(x_start_hollow, x_end_hollow):
                    self.pattern[y, x] = 0
                    self.map[y, x] = 0
                    
            self.map[y_center, x_center] = 2 if self.target_select and id == self.number else -2
            
        if self.show_path:
            for (x,y) in self.path:
                self.map[y, x] = 8
            
        if self.show_add_sub:
            destination = (self.dest_x, self.dest_y)
            self.map[self.add_sub_pos_y, self.add_sub_pos_x] = 4
            
            y_center = self.add_sub_pos_y
            x_center = self.add_sub_pos_x
            
            y_start, y_end = max(y_center - (self.thickness+self.hollow), 0), min(y_center + (self.thickness+self.hollow) + 1, self.pattern.shape[0])
            x_start, x_end = max(x_center - (self.thickness+self.hollow), 0), min(x_center + (self.thickness+self.hollow) + 1, self.pattern.shape[1])

            # 將粒子外部兩圈的開關設為開啟
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):                    
                    # 確保不影響粒子以及其周圍一圈的位置
                    if (y >= self.add_sub_pos_y - (self.hollow) and y <= self.add_sub_pos_y + (self.hollow)) and \
                    (x >= self.add_sub_pos_x - (self.hollow) and x <= self.add_sub_pos_x + (self.hollow)):
                        continue
                    self.map[y, x] = 3
        
        
        if self.target_select:
            destination = (self.dest_x, self.dest_y)
            self.map[self.dest_y, self.dest_x] = 4
            
            y_center = self.dest_y
            x_center = self.dest_x
            
            y_start, y_end = max(y_center - (self.thickness+self.hollow), 0), min(y_center + (self.thickness+self.hollow) + 1, self.pattern.shape[0])
            x_start, x_end = max(x_center - (self.thickness+self.hollow), 0), min(x_center + (self.thickness+self.hollow) + 1, self.pattern.shape[1])

            # 將粒子外部兩圈的開關設為開啟
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):                    
                    # 確保不影響粒子以及其周圍一圈的位置
                    if (y >= self.dest_y - (self.hollow) and y <= self.dest_y + (self.hollow)) and \
                    (x >= self.dest_x - (self.hollow) and x <= self.dest_x + (self.hollow)):
                        continue
                    self.map[y, x] = 3
                    
        
                    
            #self.make_route()
        #self.pattern = self.pattern.T
        #self.map = self.map.T
        
    def change_overlapping(self):
        self.overlapping = not self.overlapping
        
    def add_pattern(self):
        self.set_pattern_mode = 1
        self.video_label.bind("<Button-1>", self.on_click_set_pattern_position)
        
    def remove_pattern(self):
        self.set_pattern_mode = -1
        self.video_label.bind("<Button-1>", self.on_click_set_pattern_position)    
        
    def on_click_set_pattern_position(self, event):
        if self.set_pattern_mode == 1:
            self.show_add_sub = True
            self.root.bind("<Key>", self.adjust_pattern_position)
            x = event.x
            y = event.y
            grid_x = int(x / 512 * 128)
            grid_y = int(y / 512 * 128)
            self.add_sub_pos_x = grid_x
            self.add_sub_pos_y = grid_y
            self.generate_pattern()
            
        elif self.set_pattern_mode == -1:
            self.root.bind("<Key>", self.adjust_pattern_position)
            self.show_add_sub = True
            x = event.x
            y = event.y
            grid_x = int(x / 512 * 128)
            grid_y = int(y / 512 * 128)
            min_dis = 9999
            min_id = 1
            for id, particle in self.particle_list.items():
                start = [grid_x, grid_y]
                end = [particle.x, particle.y]
                dis = math.dist(start, end)
                min_dis = min_dis if dis>min_dis else dis
                min_id = min_id if dis>min_dis else id
            self.number = min_id
            self.add_sub_pos_x = self.particle_list[self.number].x
            self.add_sub_pos_y = self.particle_list[self.number].y
            self.generate_pattern()
            
            
    def adjust_pattern_position(self, event):
        # 在設置終點時允許使用鍵盤來微調位置
        if self.set_pattern_mode == 1:
            if event.keysym == "Up":
                self.add_sub_pos_y = max(0, self.add_sub_pos_y - 1)
            elif event.keysym == "Down":
                self.add_sub_pos_y = min(127, self.add_sub_pos_y + 1)
            elif event.keysym == "Left":
                self.add_sub_pos_x = max(0, self.add_sub_pos_x - 1)
            elif event.keysym == "Right":
                self.add_sub_pos_x = min(127, self.add_sub_pos_x + 1)
            elif event.keysym == "a":
                self.max_id += 1
                self.particle_list[self.max_id] = particles(self.add_sub_pos_x, self.add_sub_pos_y)
                self.show_add_sub = False
                self.generate_pattern()
                print(f"successfully add particle No.{self.max_id}: {self.add_sub_pos_x}, {self.add_sub_pos_y} into list")
                self.add_pattern()
            elif event.keysym == "q":
                # 完成設置位置，取消綁定事件
                self.set_pattern_mode = 0
                self.show_add_sub = False
                self.video_label.unbind("<Button-1>")
                self.root.unbind("<Key>")
                print("add particle task finish\nThank you...")
            
            self.generate_pattern()
        elif self.set_pattern_mode == -1:
            if event.keysym == "a":
                del self.particle_list[self.number]
                self.show_add_sub = False
                self.generate_pattern()
                print(f"successfully remove particle No.{self.number}: {self.add_sub_pos_x}, {self.add_sub_pos_y} into list")
                self.remove_pattern()
            elif event.keysym == "q":
                # 完成設置位置，取消綁定事件
                self.set_pattern_mode = 0
                self.show_add_sub = False
                self.video_label.unbind("<Button-1>")
                self.root.unbind("<Key>")
                print("remove particle task finish\nThank you...")
    
    def set_position_mode(self):
        # 進入設置位置的模式，並綁定滑鼠點擊事件
        self.set_position_mode_active = 1
        self.video_label.bind("<Button-1>", self.on_click_set_start_position)
        
    def set_two_merge(self):
        self.set_position_mode_active = 3
        self.video_label.bind("<Button-1>", self.on_click_set_start_position)

    def on_click_set_start_position(self, event):
        if self.set_position_mode_active == 1:
            # 計算點擊位置在 128x128 網格中的對應索引
            x = event.x
            y = event.y
            grid_x = int(x / 512 * 128)
            grid_y = int(y / 512 * 128)
            print(f"{x}, {y}\n{grid_x}, {grid_y}")
            # 設置相應的 self.map 值為 target
            min_dis = 9999
            min_id = 1
            for id, particle in self.particle_list.items():
                start = [grid_x, grid_y]
                end = [particle.x, particle.y]
                dis = math.dist(start, end)
                min_dis = min_dis if dis>min_dis else dis
                min_id = min_id if dis>min_dis else id
                
            self.number = min_id
            self.start_x = self.particle_list[self.number].x
            self.start_y = self.particle_list[self.number].y
            
            self.target_select = True
            self.generate_pattern()
            # 離開設置位置模式並取消綁定事件
            self.set_position_mode_active = 2
            self.video_label.unbind("<Button-1>")
            self.video_label.bind("<Button-1>", self.on_click_set_dest_position)
            self.root.bind("<Key>", self.adjust_dest_position)
            print("target set finish\nstart set destinition")
            
        elif self.set_position_mode_active == 3:
            # 計算點擊位置在 128x128 網格中的對應索引
            x = event.x
            y = event.y
            grid_x = int(x / 512 * 128)
            grid_y = int(y / 512 * 128)
            print(f"{x}, {y}\n{grid_x}, {grid_y}")
            # 設置相應的 self.map 值為 target
            min_dis = 9999
            min_id = 1
            for id, particle in self.particle_list.items():
                start = [grid_x, grid_y]
                end = [particle.x, particle.y]
                dis = math.dist(start, end)
                min_dis = min_dis if dis>min_dis else dis
                min_id = min_id if dis>min_dis else id
                
            self.number = min_id
            self.start_x = self.particle_list[self.number].x
            self.start_y = self.particle_list[self.number].y
            
            self.merge_target = True
            self.target_select = True
            self.generate_pattern()
            # 離開設置位置模式並取消綁定事件
            self.set_position_mode_active = 4
            self.video_label.unbind("<Button-1>")
            self.video_label.bind("<Button-1>", self.on_click_set_dest_position)
            self.root.bind("<Key>", self.adjust_dest_position)
            print("target set finish\nstart set destinition")
            
    def on_click_set_dest_position(self, event):
        if self.set_position_mode_active == 2:
            # 計算點擊位置在 128x128 網格中的對應索引
            x = event.x
            y = event.y
            grid_x = int(x / 512 * 128)
            grid_y = int(y / 512 * 128)
            self.dest_x = grid_x
            self.dest_y = grid_y
            self.generate_pattern()
            #self.video_label.unbind("<Button-1>")
            
        elif self.set_position_mode_active == 4:
            # 計算點擊位置在 128x128 網格中的對應索引
            x = event.x
            y = event.y
            grid_x = int(x / 512 * 128)
            grid_y = int(y / 512 * 128)
            print(f"{x}, {y}\n{grid_x}, {grid_y}")
            # 設置相應的 self.map 值為 target
            min_dis = 9999
            min_id = 1
            for id, particle in self.particle_list.items():
                start = [grid_x, grid_y]
                end = [particle.x, particle.y]
                dis = math.dist(start, end)
                min_dis = min_dis if dis>min_dis else dis
                min_id = min_id if dis>min_dis else id
                
            self.number2 = min_id
            self.dest_x = self.particle_list[self.number2].x
            self.dest_y = self.particle_list[self.number2].y
            self.generate_pattern()            
            
    def adjust_dest_position(self, event):
        # 在設置終點時允許使用鍵盤來微調位置
        if self.set_position_mode_active == 2:
            if event.keysym == "Up":
                self.dest_y = max(0, self.dest_y - 1)
            elif event.keysym == "Down":
                self.dest_y = min(127, self.dest_y + 1)
            elif event.keysym == "Left":
                self.dest_x = max(0, self.dest_x - 1)
            elif event.keysym == "Right":
                self.dest_x = min(127, self.dest_x + 1)
            elif event.keysym == "q":
                # 完成設置位置，取消綁定事件
                self.set_position_mode_active = 0
                self.video_label.unbind("<Button-1>")
                self.root.unbind("<Key>")
                print("destination set finish\nstart calculating path...")
                start = (self.start_x, self.start_y)
                end = (self.dest_x, self.dest_y)
                self.path = self.bfs(self.map, start, end)
                if self.path:
                    self.show_path = True
                    print(f"Route found from ({self.start_x}, {self.start_y}) to ({self.dest_x}, {self.dest_y})")
                else:
                    print(f"No route found from ({self.start_x}, {self.start_y}) to ({self.dest_x}, {self.dest_y})!")
            
            self.generate_pattern()
            
        elif self.set_position_mode_active == 4:
            if event.keysym == "q":
                # 完成設置位置，取消綁定事件
                self.set_position_mode_active = 0
                self.video_label.unbind("<Button-1>")
                self.root.unbind("<Key>")
                print("destination set finish\nstart calculating path...")
                start = (self.start_x, self.start_y)
                end = (self.dest_x, self.dest_y)
                self.path = self.bfs(self.map, start, end)
                if self.path:
                    self.show_path = True
                    print(f"Route found from ({self.start_x}, {self.start_y}) to ({self.dest_x}, {self.dest_y})")
                else:
                    print(f"No route found from ({self.start_x}, {self.start_y}) to ({self.dest_x}, {self.dest_y})!")
            
            self.generate_pattern()
                
    def bfs(self, maze, start, end):
        rows, cols = maze.shape
        visited = set([start])
        queue = deque([start])
        parents = {start: None}

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        while queue:
            x, y = queue.popleft()

            if (x, y) == end:
                path = []
                while (x, y) != start:  # Change to stop at the start node
                    path.append((x, y))
                    x, y = parents[(x, y)]
                path.append(start)  # Add the start node to the path
                return path[::-1]

            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                if 0 <= nx < rows and 0 <= ny < cols and maze[ny, nx] != -3 and (nx, ny) not in visited:
                    parents[(nx, ny)] = (x, y)
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return None
    
    def move_cell_window(self, G_var):
        self.start_move = True
        self.route_index = 0
        folder_path = "./pattern/cell_control/"
        self.clear_csv_files(folder_path)
        print("Start moving")
        self.perform_movement(G_var)
            
    def perform_movement(self, G_var):
        if self.start_move:
            self.generateMovement(G_var)
            Func_update_pattern_image(self.pattern, G_var)
            # 每隔 1000 毫秒重新調用自己
            self.root.after(100, lambda: self.perform_movement(G_var))

    
    def generateMovement(self, G_var: Global_Var):
        
        #start = tuple(map(tuple, np.argwhere(path == 2)))[0]
        #end = tuple(map(tuple, np.argwhere(path == 4)))[0]
        #print(f"route index = {self.route_index}")
        # 移动粒子
        if self.start_move :
            self.route_index += 1
            
            if self.route_index >= len(self.path):
                self.route_index = len(self.path)-1
                self.start_move = False
                self.target_select = False
                self.merge_target = False
                G_var.dragdrop_app.confirm_create_action("DEP", "Single Move", "./pattern/cell_control/", 1, 0, 1, 5, "MHz", 180, 1.8, G_var)

            if self.merge_target and self.route_index + 3 >= len(self.path):
                self.route_index = len(self.path)-1 - 3
                self.start_move = False
                self.target_select = False
                self.merge_target = False
                G_var.dragdrop_app.confirm_create_action("DEP", "Merge", "./pattern/cell_control/", 1, 0, 1, 5, "MHz", 180, 1.8, G_var)
                
            
            x, y = self.path[self.route_index]

            #if self.route_index > 0:  # 如果不是起点，则将上一个位置恢复为0
            prev_x, prev_y = self.path[self.route_index - 1]
            #if (prev_x, prev_y) != start and (prev_x, prev_y) != end:
            self.map[prev_y, prev_x] = -1
            '''
            if self.show_add_sub:
            destination = (self.dest_x, self.dest_y)
            self.map[self.add_sub_pos_y, self.add_sub_pos_x] = 4
            
            y_center = self.add_sub_pos_y
            x_center = self.add_sub_pos_x
            
            y_start, y_end = max(y_center - (self.thickness+self.hollow), 0), min(y_center + (self.thickness+self.hollow) + 1, self.pattern.shape[0])
            x_start, x_end = max(x_center - (self.thickness+self.hollow), 0), min(x_center + (self.thickness+self.hollow) + 1, self.pattern.shape[1])

            # 將粒子外部兩圈的開關設為開啟
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):                    
                    # 確保不影響粒子以及其周圍一圈的位置
                    if (y >= self.add_sub_pos_y - (self.hollow) and y <= self.add_sub_pos_y + (self.hollow)) and \
                    (x >= self.add_sub_pos_x - (self.hollow) and x <= self.add_sub_pos_x + (self.hollow)):
                        continue
                    self.map[y, x] = 3
            '''
            
            
            # 計算擴大後的粒子周圍座標範圍
            y_start_prev, y_end_prev = max(prev_y - (self.thickness+self.hollow), 0), min(prev_y + (self.thickness+self.hollow+1), self.pattern.shape[0])
            x_start_prev, x_end_prev = max(prev_x - (self.thickness+self.hollow), 0), min(prev_x + (self.thickness+self.hollow+1), self.pattern.shape[1])
            
            # 將粒子外部兩圈的開關設為開啟
            for y_prev in range(y_start_prev, y_end_prev):
                for x_prev in range(x_start_prev, x_end_prev):
                    
                    # 確保不影響粒子以及其周圍一圈的位置
                    # if (y_prev >= prev_y - (1+patt_blank) and y_prev <= prev_y + (1+patt_blank)) and \
                    # (x_prev >= prev_x - (1+patt_blank) and x_prev <= prev_x + (1+patt_blank)):
                    #     continue
                    if( self.map[y_prev, x_prev] != -1):
                        self.pattern[y_prev, x_prev] = 0
                        self.map[y_prev, x_prev] = 0
            
            
            self.map[y, x] = 2
            
            #重設終點的pattern
            if self.merge_target:
                
                self.map[self.dest_y, self.dest_x] = 4
                
                y_center = self.dest_y
                x_center = self.dest_x
                
                y_start_des, y_end_des = max(y_center - (self.thickness+self.hollow), 0), min(y_center + (self.thickness+self.hollow) + 1, self.pattern.shape[0])
                x_start_des, x_end_des = max(x_center - (self.thickness+self.hollow), 0), min(x_center + (self.thickness+self.hollow) + 1, self.pattern.shape[1])

                # 將粒子外部兩圈的開關設為開啟
                for y_des in range(y_start_des, y_end_des):
                    for x_des in range(x_start_des, x_end_des):                    
                        # 確保不影響粒子以及其周圍一圈的位置
                        #if (y_des >= self.dest_y - (self.hollow) and y_des <= self.dest_y + (self.hollow)) and \
                        #(x_des >= self.dest_x - (self.hollow) and x_des <= self.dest_x + (self.hollow)):
                        #    continue
                        self.map[y_des, x_des] = 5
            
            
            
            # 計算擴大後的粒子周圍座標範圍
            y_start, y_end = max(y - (self.thickness+self.hollow), 0), min(y + (self.thickness+self.hollow+1), self.pattern.shape[0])
            x_start, x_end = max(x - (self.thickness+self.hollow), 0), min(x + (self.thickness+self.hollow+1), self.pattern.shape[1])
            
            # 將粒子外部兩圈的開關設為開啟
            for y_now in range(y_start, y_end):
                for x_now in range(x_start, x_end):
                    
                    # 確保不影響粒子以及其周圍一圈的位置
                    if (y_now >= y - (self.hollow) and y_now <= y + (self.hollow)) and \
                    (x_now >= x - (self.hollow) and x_now <= x + (self.hollow)):
                        continue
                    
                    if self.map[y_now, x_now] == 5:
                        self.pattern[y_now, x_now] = 0
                    else:
                        self.pattern[y_now, x_now] = 1
                        
                                        
                    if( self.map[y_now, x_now] != -1):
                        self.map[y_now, x_now] = 1
                    
            self.map[prev_y, prev_x] = 0
            
            
            
            csv_filename2 = f"./pattern/cell_control/path_{self.route_index}.csv"
            with open(csv_filename2, mode='w', newline='') as file:
                writer = csv.writer(file)
                #corr_patt = pattern.T
                # 將每一列 (list) 寫入 CSV 檔案
                for row in self.pattern:
                    writer.writerow(row)
            
            print(f"Written{self.route_index} Done!")
            
            
            
            #self.updateFrame()
            
    def clear_csv_files(self, folder_path):
        # 找到資料夾中所有 .csv 檔案
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        
        # 刪除每個 .csv 檔案
        for file_path in csv_files:
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
    
    #def connect_to_obs(self):
    #    try:
    #        self.ws = obsws("localhost", 4455, "c8FpDwW3bVJVz9OA")  # 替換為你的 OBS WebSocket 密碼
    #        self.ws.connect()
    #        print("Connecting to OBS WebSocket...")
#
    #        # 查詢當前場景列表
    #        scenes = self.ws.call(obswebsocket.requests.GetSceneList())
    #        print(f"Connected to OBS. Current Scene: {scenes.get_current_scene()}")
#
    #        # 獲取當前的視頻來源
    #        current_source = self.ws.call(obswebsocket.requests.GetCurrentScene()).get_name()
    #        print(f"Current source: {current_source}")
#
    #        # 監聽 OBS 狀態變化事件
    #        self.ws.register(self.on_event, obswebsocket.events.SwitchScenes)
    #    except Exception as e:
    #        print(f"Failed to connect to OBS: {e}")
    #        self.show_placeholder_image()

    def on_event(self, message):
        # 處理 OBS 的場景變化事件
        print(f"Switching to scene: {message.get_scene_name()}")
        self.update_obs_stream(message.get_scene_name())

    def update_obs_stream(self, scene_name):
        # 根據不同的場景名稱更新 OBS 畫面顯示
        if scene_name == "Your OBS Scene Name":
            # 在此處添加你的邏輯來檢查 OBS 畫面來源
            print("OBS scene detected, updating video label.")
        else:
            self.show_placeholder_image()

    def show_placeholder_image(self):
        # 顯示更淺的灰色佔位圖像
        lighter_gray = (211, 211, 211)  # 淺灰色 (RGB)
        placeholder = Image.new("RGB", (512, 512), color=lighter_gray)
        img_tk = ImageTk.PhotoImage(placeholder)
        self.video_label.imgtk = img_tk
        self.video_label.config(image=img_tk)

    def close_obs_connection(self):
        # 在應用關閉時關閉 OBS WebSocket 連接
        if hasattr(self, 'ws'):
            self.ws.disconnect()
