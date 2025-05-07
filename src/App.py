# ========================================================
# Project:  BioFPGAG-G6-python
# File:     App.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================

# ========================================================
# DragDropApp Class
# ========================================================
# DragDropApp is the main GUI class that handles protocol creation and display
# support the drag and drop actions
# ========================================================

from src.header import *
from src.Protocol import *
from src.Chip import *
from src.console import *
from src.loop_setting import *
from src.script import *

class DragDropApp:
    def __init__(self, root: tk.Tk, G_var: Global_Var):
        self.root = root
        self.root.title("Enhanced Drag and Drop with Overlap Check")
        self.action_window = None  # 用來記錄當前打開的 Action 視窗 
        # 初始化狀態值
        self.status_values = {
            "action_name": "N/A",
            "cur_iter": "0",
            "total_iter": "0",
            "cur_pattern_no": "0",
            "total_num_pattern": "0",
            "interval": "0",
            "time_stamp": "0",
            "ad2_output": "Stopped",
            "frequency": "N/A",
            "phase_p0": "0",
            "phase_p1": "N/A",
            "voltage": "N/A",
            "cs_mode": "N/A",
            "start": "",
            "end": "",
            "step": "",
            "ms_times": "",
            "temperature": "37"
        }

        if AD2_ON:
            self.status_values["ad2_device"] = "N/A"
        
        self.protocol = Protocol(G_var)
        self.selected_action = None  # 用來記錄當前選中的 Action

        # 建立菜單欄
        self.create_menu(G_var)

        # 主畫布區域
        self.canvas = tk.Canvas(self.root, width=800, height=700, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 繪製大框架和標題
        self.create_protocol_frame(G_var)

        self.dep_steps = []  # To store DEP Action steps
        self.heating_steps = []  # To store Heating Action steps
        self.cs_steps = []  # To store CS Action steps
        self.texts = []
        self.arrows = []
        self.drag_data = {"x": 0, "y": 0, "item": None, "start_y": 0, "text_id": None}
        
        # 在初始化中調用快捷鍵綁定
        self.setup_key_bindings(G_var)

        # [Bug Fixed] 修復首次使用快捷鍵沒有反應的問題
        self.root.focus_force()

        # 啟動AD2
        if AD2_ON:
            self.change_ad2_status(G_var)

# =================================================================================================
# GUI Functions
# =================================================================================================
    #########################
    # Create Protocol Frame
    #########################
    def create_protocol_frame(self, G_var: Global_Var):
        # 大框架
        self.canvas.create_rectangle(20, 20, 380, 580, outline="black", width=2)
        self.canvas.create_text(200, 40, text="Bio Protocol", font=("Helvetica", 16, "bold"))
        self.canvas.create_text(100, 60, text="Name:", anchor="w")
        self.protocol_name_txt = self.canvas.create_text(300, 60, text=self.protocol.name, anchor="e")
        self.canvas.create_text(100, 80, text="Version:", anchor="w")
        self.protocol_ver_txt = self.canvas.create_text(300, 80, text=self.protocol.version, anchor="e")
        G_var.canvas = self.canvas

        # 添加子畫布
        self.sub_canvas = tk.Canvas(self.root, width=350, height=460, bg="white", borderwidth=0, border=0, highlightthickness=0)

        # 綁定事件
        self.sub_canvas.bind("<ButtonPress-1>", self.on_start)
        self.sub_canvas.bind("<B1-Motion>", self.on_drag)
        self.sub_canvas.bind("<ButtonRelease-1>", lambda event: self.on_drop(event,G_var))
        self.sub_canvas.bind("<Double-1>",  lambda event: self.on_double_click(event,G_var))
        self.sub_canvas.bind("<Button-3>", lambda event: self.on_start(event, right_click=True))

        # 滾動條
        self.scroll_bar = tk.Scrollbar(self.sub_canvas, orient="vertical", command=self.sub_canvas.yview)
        self.scroll_bar.place(relx=1, rely=0, relheight=1, anchor="ne")
        self.sub_canvas.configure(yscrollcommand=self.scroll_bar.set)
        
        # 將子畫布添加到主畫布上
        self.canvas.create_window(25, 100, window=self.sub_canvas, anchor="nw")

        # 狀態顯示
        G_var.status_text_id = self.canvas.create_text(200, 570, text="Ready", font=("Helvetica", 10), fill="black", anchor="center")

        # 添加 "Running Status" 框架
        self.canvas.create_rectangle(420, 20, 780, 580, outline="black", width=2)
        self.canvas.create_text(600, 40, text="Running Status", font=("Helvetica", 16, "bold"))

        # 初始化狀態行
        self.status_lines = {}  # 初始化為字典
        self.status_start_y = 60
        self.status_line_height = 25

        # 定義淡色系背景顏色（Morandi調色板）
        section_colors = ["#D7E3E9", "#D7E9E3", "#E9E3D7", "#E9D7E3"]

        # 定義 Running Status 層次結構
        running_status = [
            {"title": "DEP Action", "fields": [
                {"label": "Action Name", "value_keys": ["action_name"], "format": "{0}"},
                {"label": "Current Iteration", "value_keys": ["cur_iter", "total_iter"], "format": "{0} of {1}"},
                {"label": "Current Pattern No.", "value_keys": ["cur_pattern_no", "total_num_pattern", "interval"],
                "format": "{0} of {1} with {2} ms delay"},
                {"label": "Time Stamp", "value_keys": ["time_stamp"], "format": "{0} s"}
            ]},
            {"title": "AD2", "fields": [
                {"label": "AD2 Device", "value_keys": ["ad2_device"], "format": "{0}"},
                {"label": "Output Function", "value_keys": ["ad2_output"], "format": "{0}"},
                {"label": "Output Frequency", "value_keys": ["frequency"], "format": "{0} Hz"},
                {"label": "Output Phase", "value_keys": ["phase_p0", "phase_p1"], "format": "P0: {0}°, P1: {1}°"},
                {"label": "Output Voltage", "value_keys": ["voltage"], "format": "{0} V"}
            ]},
            {"title": "Cap. Sensing", "fields": [
                {"label": "Delay", "value_keys": ["start", "end", "step"], "format": "Start: {0}, End: {1}, Step: {2}"},
                {"label": "Multiple Sampling", "value_keys": ["ms_times"], "format": "{0}"}
            ]},
            {"title": "Thermal Control", "fields": [
                {"label": "Temperature", "value_keys": ["temperature"], "format": "{0} °C"}
            ]}
        ]

        # 動態生成階層式狀態行，並添加背景顏色
        step = 20
        padding = 10
        for idx, section in enumerate(running_status):
            # 背景框
            color = section_colors[idx % len(section_colors)]  # 按順序循環使用顏色
            start_y = self.status_start_y
            end_y = start_y + self.status_line_height * (len(section["fields"]) + 1) + padding
            self.create_rounded_rectangle(self.canvas, 440, start_y, 760, end_y, fill=color, tags="")

            # 子標題
            title_id = self.canvas.create_text(450, padding + self.status_start_y, text=section["title"],
                                            font=("Helvetica", 12, "bold"), anchor="nw")
            self.status_start_y += padding + self.status_line_height

            # 字段
            for field in section["fields"]:
                label = field["label"]
                value_keys = field["value_keys"]
                value_format: str = field["format"]

                # 初始化值為 N/A
                values = [self.status_values.get(key, "N/A") for key in value_keys]
                text = f"{label}: {value_format.format(*values)}"

                text_id = self.canvas.create_text(450, self.status_start_y, text=text,
                                                font=("Arial", 10), anchor="nw")
                for key in value_keys:
                    self.status_lines[key] = (label, text_id, value_keys, value_format)
                self.status_start_y += self.status_line_height
            self.status_start_y += step

        # 添加運行控制按鈕
        self.add_control_buttons(G_var)
        # self.add_status_buttons(G_var)

    def update_DEP_time_stamp(self):
        self.update_status_frame("time_stamp", f"{time.time() - self.protocol.launch_time_stamp:.2f}")
        
    def update_DEP_status_frame(self, action_name, cur_iter, total_iter, cur_pattern_no, total_num_pattern, interval):
        self.update_status_frame("action_name", action_name)
        self.update_status_frame("cur_iter", cur_iter)
        self.update_status_frame("total_iter", total_iter)
        self.update_status_frame("cur_pattern_no", cur_pattern_no)
        self.update_status_frame("total_num_pattern", total_num_pattern)
        self.update_status_frame("interval", interval)
        self.update_status_frame("time_stamp", f"{time.time() - self.protocol.launch_time_stamp:.2f}")

    def update_AD2_status_frame(self, switch, frequency, phase_p1, voltage):
        self.update_status_frame("ad2_output", "Stopped" if (not switch) else "Sine")
        frequeny_format = ''
        if frequency != 'N/A':
            frequeny_format = format_number(frequency)
        else:
            frequeny_format = '0'
        self.update_status_frame("frequency", frequeny_format)
        self.update_status_frame("phase_p1", phase_p1)
        self.update_status_frame("voltage", voltage)
    
    def update_status_frame(self, key, value):
        """
        更新指定字段的值並刷新顯示。

        :param key: 字段名稱（如 "action_name"）
        :param value: 要更新的值
        """
        if key in self.status_values:
            self.status_values[key] = value
            # [revised] 更新所有受影響的行
            label, text_id, value_keys, value_format = self.status_lines[key]
            values = [self.status_values.get(k, "N/A") for k in value_keys]
            text = f"{label}: {value_format.format(*values)}"
            self.canvas.itemconfig(text_id, text=text)

        else:
            print(f"Unknown status key: {key}")
            
    def add_status_buttons(self, G_var):
        # AD2 Output 開關按鈕
        ad2_button = tk.Button(self.root, text="Toggle AD2 Output", command=lambda: self.toggle_ad2_output(G_var))
        ad2_button.place(x=650, y=100, width=120, height=30)

        # Cap. Sensing 模式選擇按鈕
        mode_button = tk.Button(self.root, text="Set CS Mode", command=lambda: self.set_cs_mode(G_var))
        mode_button.place(x=650, y=200, width=120, height=30)

        # Thermal Control 溫度設置按鈕
        temp_button = tk.Button(self.root, text="Set Temperature", command=lambda: self.set_temperature(G_var))
        temp_button.place(x=650, y=300, width=120, height=30)
    
    def add_control_buttons(self, G_var):
        # 第一行按钮 - Run Protocol 和 Run Selected
        run_button = tk.Button(self.root, text="Run Protocol", font=("Helvetica", 12, "bold"),
                            bg="#4CAF50", fg="white", relief=tk.RAISED, borderwidth=3, highlightthickness=3,
                            command=lambda: self.call_run_protocol(G_var))
        run_button.place(x=80, y=600, width=120, height=40)

        run_selected_button = tk.Button(self.root, text="Run Selected", font=("Helvetica", 12, "bold"),
                                        bg="#FF9800", fg="white", relief=tk.RAISED, borderwidth=3, highlightthickness=3,
                                        command=lambda: self.call_run_selected_action(G_var))
        run_selected_button.place(x=220, y=600, width=120, height=40)

        # 第二行按钮 - Pause/Resume 和 Stop
        self.pause_button = tk.Button(self.root, text="Pause", font=("Helvetica", 12, "bold"),
                                    bg="#D0D0D0", fg="white", relief=tk.RAISED, borderwidth=3, highlightthickness=3,
                                    command=lambda: self.toggle_pause(G_var))
        self.pause_button.place(x=80, y=650, width=120, height=40)

        self.stop_button = tk.Button(self.root, text="Stop", font=("Helvetica", 12, "bold"),
                                    bg="#D0D0D0", fg="white", relief=tk.RAISED, borderwidth=3, highlightthickness=3,
                                    command=lambda: self.stop_action(G_var, user_stop=True))
        self.stop_button.place(x=220, y=650, width=120, height=40)

    
    #########################
    # Update GUI Action
    #########################
    def update_gui_from_protocol(self,G_var):
        self.canvas.itemconfig(self.protocol_name_txt, text=self.protocol.name)
        self.canvas.itemconfig(self.protocol_ver_txt, text=self.protocol.version)
        self.sub_canvas.delete("all")  # 清空畫布
        self.dep_steps.clear()
        # 繪製所有 Action
        for i, action in enumerate(self.protocol.actions):
            self.create_step(action.get_action_label(), 50-25, i * 100)
        # 更新箭頭和編號
        self.update_arrows()
        self.update_numbers()
        # 更新滾動條
        self.update_scrollbar()

    #########################
    # Bind Key Shortcuts
    #########################
    # 定義快捷鍵綁定的方法
    def setup_key_bindings(self,G_var):
        self.root.bind("q", lambda event: self.show_properties(G_var))
        self.root.bind("p", lambda event: self.run_script(G_var))
        self.root.bind("<Delete>", lambda event: self.delete_action(G_var))

# =================================================================================================
# Menu Functions
# =================================================================================================
    #########################
    # Create Menu
    #########################
    def create_menu(self,G_var: Global_Var):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Protocol", menu=file_menu)
        file_menu.add_command(label="Create Protocol", command=lambda: self.create_protocol(G_var))
        file_menu.add_separator()
        file_menu.add_command(label="Load Protocol", command= lambda: self.load_protocol(G_var))
        file_menu.add_separator()
        file_menu.add_command(label="Save Protocol", command= lambda: self.save_protocol(G_var))
        file_menu.add_separator()
        file_menu.add_command(label="Rename Protocol", command= lambda: self.rename_protocol(G_var))
        file_menu.add_command(label="Rename Version", command= lambda: self.rename_version(G_var))
        file_menu.add_separator()
        file_menu.add_command(label="Update GUI", command= lambda: self.update_gui_from_protocol(G_var))
        file_menu.add_separator()
        file_menu.add_command(label="Open New Display", command= lambda: self.protocol.open_new_dual_display(G_var))

        # Actions Menu
        actions_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Actions", menu=actions_menu)
        actions_menu.add_command(label="Add DEP Action", command= lambda: self.add_dep_action(G_var))
        actions_menu.add_command(label="Add Wait Action", command= lambda: self.add_wait_action(G_var))
        actions_menu.add_separator()
        actions_menu.add_command(label="Delete Selected Action", command= lambda: self.delete_action(G_var))
        actions_menu.add_separator()
        actions_menu.add_command(label="Show Selected Info", command= lambda: self.show_properties(G_var))

        # Run Menu
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Protocol", command= lambda: self.call_run_protocol(G_var))
        run_menu.add_command(label="Run Protocal with loop", command= lambda: self.call_run_protocol_with_loop(G_var))
        run_menu.add_command(label="Run Selected Action", command= lambda: self.call_run_selected_action(G_var))
        run_menu.add_separator()
        run_menu.add_command(label="Show Protocol", command=lambda: self.protocol.print_protocol(G_var))
        run_menu.add_separator()
        run_menu.add_command(label="Run BIST", command= lambda: self.run_bist())

        # AD2 Menu
        if AD2_ON:
            ad2_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="AD2", menu=ad2_menu)
            ad2_menu.add_command(label="Enable/Disable AD2", command=lambda :self.change_ad2_status(G_var))
            ad2_menu.add_separator()
            ad2_menu.add_command(label="Turn off Sine Wave", command= lambda: self.turn_off_ad2_output(G_var))
            ad2_menu.add_separator()
            ad2_menu.add_command(label="Set Global Frequency", command= self.set_global_frequency)
            ad2_menu.add_command(label="Set Global Phase", command= self.set_global_phase)
            ad2_menu.add_command(label="Set Global Voltage", command= self.set_global_voltage)

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Add Command", command= lambda: self.run_script(G_var))
        tools_menu.add_command(label="Console", command= lambda: self.launch_console(G_var))
        tools_menu.add_separator()
        tools_menu.add_command(label="Debug", command= lambda: self.open_debug_window())
        tools_menu.add_separator()
        tools_menu.add_command(label="Reset", command= lambda: self.reset_system(G_var))

        # Context Menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete", command= lambda: self.delete_action(G_var))

    #########################
    # AD2
    #########################
    def change_ad2_status(self, G_var: Global_Var):
        if G_var.ad2_enable:
            G_var.ad2.close_device()
            self.update_status_frame("ad2_device", "Disconnected")
            messagebox.showinfo("AD2 Connection", "AD2 has been closed.")
            G_var.ad2_enable = False
        else:
            try:
                G_var.ad2.open_device()
            except RuntimeError as e:
                print(bcolors.ERROR + '[ERROR] ' + str(e) + bcolors.RESET)
                messagebox.showerror("AD2 Connection Error", str(e))
            else:
                G_var.ad2_enable = True
                self.update_status_frame("ad2_device", "Connected")
                messagebox.showinfo("AD2 Connection", "Your AD2 device is connected!")

        

    def set_global_frequency(self):
        new_freq = simpledialog.askstring("Set Global Frequency", "Enter a new frequency (Hz):")
        if new_freq:
            for action in self.protocol.actions:
                try:
                    action.action_frequency = parse_number(new_freq)
                except ValueError:
                    messagebox.showerror("Invalid Frequency", "Please enter a valid frequency value.")
                    return

    def set_global_phase(self):
        new_phase = simpledialog.askstring("Set Global Phase", "Enter a new phase (degrees):")
        if new_phase:
            for action in self.protocol.actions:
                try:
                    action.action_phase = float(new_phase)
                except ValueError:
                    messagebox.showerror("Invalid Phase", "Please enter a valid phase value.")
                    return

    def set_global_voltage(self):
        new_voltage = simpledialog.askstring("Set Global Voltage", "Enter a new voltage (Vpp):")
        if new_voltage:
            for action in self.protocol.actions:
                try:
                    action.action_voltage = float(new_voltage)
                except ValueError:
                    messagebox.showerror("Invalid Voltage", "Please enter a valid voltage value.")
                    return

    def turn_off_ad2_output(self, G_var: Global_Var):
        G_var.ad2.stop_waveform()
        self.update_AD2_status_frame(False, 'N/A', 'N/A', 'N/A')

    #########################
    # Debugger
    #########################
    def open_debug_window(self):
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Debug")
        debug_window.geometry("400x50")
        tk.Label(debug_window, text="Command:").pack()
        self.cmdLabel = tk.Entry(debug_window, width=400, bd=5)
        self.cmdLabel.focus_set()
        self.cmdLabel.pack()
        debug_window.bind("<Return>", lambda event: self.debug_cmd())

    def debug_cmd(self):
        if DEVELOP_MODE:
            try:
                tmp_command = self.cmdLabel.get()
                eval(tmp_command)
            except Exception:
                print("Command Error")
            else:
                print('[CMD]', tmp_command)
                self.cmdLabel.delete(0, tk.END)
    
    #########################
    # Run DEP BIST
    #########################
    def run_bist(self):
        # Run Built-In Self-Test (BIST) for the chip
        # Read pattern from csv file
        pattern = np.genfromtxt('./pattern/bist_pattern.csv', delimiter=',', dtype=int)
        pattern = pattern.astype(bool)
        print(bcolors.STATUS + "[Info] Running Built-In Self-Test (BIST)..." + bcolors.RESET)
        if RPI_ON:
            output = BIST(pattern)
        else:
            print(bcolors.ERROR + "RASPBERRY_PI_IP is not defined in header.py" + bcolors.RESET)
            output = np.zeros((128, 128), dtype=bool)
        display_patterns_in_gui(pattern,output, self.run_bist)

    #########################
    # Reset System
    #########################
    def reset_system(self, G_var: Global_Var):
        self.stop_action(G_var)
        update_status(G_var,"Ready")
        Func_update_pattern_image(np.zeros((128, 128), dtype=bool), G_var)
        if RPI_ON:
            reset_chip_on_pi()    
            print(bcolors.STATUS + "[Info] Chip reset." + bcolors.RESET)
        else:
            print(bcolors.ERROR + "RASPBERRY_PI_IP is not defined in header.py" + bcolors.RESET)

    #########################
    # Stop Button Action
    #########################
    def stop_action(self, G_var: Global_Var, user_stop=False):
        try:
            G_var.display_window.after_cancel(G_var.pending_id)
        except ValueError:
            pass
        G_var.is_paused = False
        G_var.is_stopped = True
        G_var.is_running = False
        G_var.pause_sec = 0
        self.pause_button.config(text="Pause", bg="#D0D0D0")
        print("Action stopped.")
        status_text = "Protocol/Action stopped."
        update_status(G_var,status_text)
        if user_stop: 
            self.turn_off_ad2_output(G_var)

    #########################
    # Pause/Resume Button Action
    #########################
    def toggle_pause(self, G_var: Global_Var):
        if G_var.is_stopped:
            return
        if G_var.is_paused:
            G_var.is_paused = False
            self.pause_button.config(text="Pause", bg="#D0D0D0")
            print("Resumed")
            status_text = "Protocol/Action resumed."
            update_status(G_var,status_text)
        else:
            G_var.is_paused = True
            self.pause_button.config(text="Resume", bg="#4CAF50")
            print("Paused")
            status_text = "Protocol/Action paused."
            update_status(G_var,status_text)

# =================================================================================================
# Protocol Functions
# =================================================================================================
    #########################
    # Save Protocol Action
    #########################
    def save_protocol(self,G_var):
        # 設置預設的檔案名稱
        default_filename = f"{self.protocol.name}_{self.protocol.version}.json"
        filename = filedialog.asksaveasfilename(initialdir="./bio-protocol",defaultextension=".json", initialfile=default_filename)
        if filename:
            self.protocol.save_protocol_to_json(filename)
            print(bcolors.OK + f"[Success] Protocol saved to {filename}." + bcolors.RESET)
    
    #########################
    # Load Protocol Action
    #########################
    def load_protocol(self,G_var,filename=None):
        if not filename:
            filename = filedialog.askopenfilename(initialdir="./bio-protocol", filetypes=[("JSON files", "*.json")])
        if filename and os.path.exists(filename):
            self.protocol.load_protocol_from_json(filename)
            self.update_gui_from_protocol(G_var)
            print(bcolors.OK + f"[Success] Protocol loaded from {filename}." + bcolors.RESET)
        else:
            print(bcolors.ERROR + f"[Error] File {filename} does not exist." + bcolors.RESET)

    #########################
    # Create New Protocol Action
    #########################
    def create_protocol(self,G_var):
        # 彈出對話框輸入 Protocol Name 和 Version
        protocol_name = simpledialog.askstring("Create Protocol", "Enter new protocol name:")
        protocol_version = simpledialog.askstring("Create Protocol", "Enter new protocol version:")

        if protocol_name and protocol_version:
            # 重置 Protocol 
            # [Bug Fixed] 修復出現兩個 Protocol 的問題
            self.protocol.reset_protocol(G_var) 
            self.protocol.name = protocol_name
            self.protocol.version = protocol_version

            # 更新 GUI 畫面
            self.update_gui_from_protocol(G_var)

    #########################
    # Rename Protocol Action
    #########################
    def rename_protocol(self, G_var):
        new_name = simpledialog.askstring("Rename Protocol", "Enter new protocol name:")
        if new_name:
            self.protocol.name = new_name
            self.canvas.itemconfig(self.protocol_name_txt, text=new_name)

    #########################
    # Rename Version Action
    #########################
    def rename_version(self, G_var):
        new_version = simpledialog.askstring("Rename Version", "Enter new version:")
        if new_version:
            self.protocol.version = new_version
            self.canvas.itemconfig(self.protocol_ver_txt, text=new_version)


# =================================================================================================
# Create / Delete Action Functions
# =================================================================================================
    #########################
    # Add DEP Action
    #########################
    def add_dep_action(self, G_var):
        self.add_action("DEP", G_var)

    #########################
    # Add Wait Action
    #########################
    def add_wait_action(self, G_var):
        # Add wait action or other action types in the future.
        self.add_action("WAIT", G_var)

    #########################
    # Add DEP/Wait Action Frame
    #########################
    def add_action(self, action_type, G_var):
        # 根據選擇的 Action 類型創建新 Action 視窗
        self.action_window = tk.Toplevel(self.root)
        self.action_window.title(f"Create {action_type} Action")

        # 設置統一字體
        font_style = ("Helvetica", 12)

        # 使用 LabelFrame 來包裹所有輸入字段
        action_frame = tk.LabelFrame(self.action_window, text=f"New {action_type} Action", font=("Helvetica", 14, "bold"))
        action_frame.pack(fill="both", expand="yes", padx=20, pady=20)

        # Action Name
        tk.Label(action_frame, text="Action Name:", font=font_style).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        action_name_entry = tk.Entry(action_frame, font=font_style)
        action_name_entry.grid(row=0, column=1, padx=10, pady=5)
        action_name_entry.insert(0, action_type + "_Action_" + str(len(self.protocol.actions)+1))
        action_name_entry.focus_set()

        if action_type == "DEP":
            # Folder Path
            tk.Label(action_frame, text="Folder Path:", font=font_style).grid(row=1, column=0, padx=10, pady=5, sticky="w")
            folder_path_entry = tk.Entry(action_frame, font=font_style)
            folder_path_entry.grid(row=1, column=1, padx=10, pady=5)

            # Browse Button for Folder Path
            folder_path_button = tk.Button(action_frame, text="Browse...", font=font_style, command=lambda: self.open_dep_pattern_folder(folder_path_entry))
            folder_path_button.grid(row=1, column=2, padx=10, pady=5)

            # Pattern Interval 
            tk.Label(action_frame, text="Pattern Interval (s):", font=font_style).grid(row=2, column=0, padx=10, pady=5, sticky="w")
            pattern_interval_entry = tk.Entry(action_frame, font=font_style)
            pattern_interval_entry.grid(row=2, column=1, padx=10, pady=5)
            # set default value
            pattern_interval_entry.insert(0, "0.5")
            
            # Timer Mode
            timer_mode_dropdown = ttk.Combobox(action_frame, values=["Correct", "Normal"], font=('Arial',10), width=8, state="readonly")
            timer_mode_dropdown.set("Correct")
            timer_mode_dropdown.grid(row=2, column=2, padx=10, pady=5)

            # Loop Iterations
            tk.Label(action_frame, text="Loop Iterations (times):", font=font_style).grid(row=3, column=0, padx=10, pady=5, sticky="w")
            loop_iterations_entry = tk.Entry(action_frame, font=font_style)
            loop_iterations_entry.grid(row=3, column=1, padx=10, pady=5)
            # set default value
            loop_iterations_entry.insert(0, "1")

            # Loop Interval
            tk.Label(action_frame, text="Loop Interval (s):", font=font_style).grid(row=4, column=0, padx=10, pady=5, sticky="w")
            loop_interval_entry = tk.Entry(action_frame, font=font_style)
            loop_interval_entry.grid(row=4, column=1, padx=10, pady=5)
            # set default value
            loop_interval_entry.insert(0, "0")

            # Frequency Entry and Unit Dropdown (Hz, kHz, MHz)
            tk.Label(action_frame, text="Frequency:", font=font_style).grid(row=5, column=0, padx=10, pady=5, sticky="w")
            frequency_entry = tk.Entry(action_frame, font=font_style)
            frequency_entry.grid(row=5, column=1, padx=10, pady=5)
            frequency_entry.insert(0, "1")

            # Frequency Unit Dropdown
            frequency_unit_dropdown = ttk.Combobox(action_frame, values=["Hz", "kHz", "MHz"], font=font_style, width=6, state="readonly")
            frequency_unit_dropdown.set("MHz")
            frequency_unit_dropdown.grid(row=5, column=2, padx=10, pady=5)

            # Phase Entry
            tk.Label(action_frame, text="Phase (deg):", font=font_style).grid(row=6, column=0, padx=10, pady=5, sticky="w")
            phase_entry = tk.Entry(action_frame, font=font_style)
            phase_entry.grid(row=6, column=1, padx=10, pady=5)
            phase_entry.insert(0, "180")

            # Voltage Entry
            tk.Label(action_frame, text="Voltage (Vpp):", font=font_style).grid(row=7, column=0, padx=10, pady=5, sticky="w")
            voltage_entry = tk.Entry(action_frame, font=font_style)
            voltage_entry.grid(row=7, column=1, padx=10, pady=5)
            voltage_entry.insert(0, "1.8")


        # Confirm and Cancel Buttons
        button_frame = tk.Frame(self.action_window)
        button_frame.pack(pady=20)

        command = lambda: self.confirm_create_action(action_type, action_name_entry.get(), 
                                                     folder_path_entry.get(), 
                                                     pattern_interval_entry.get(),
                                                     timer_mode_dropdown.get(),
                                                     loop_interval_entry.get(), 
                                                     loop_iterations_entry.get(),
                                                     frequency_entry.get(),
                                                     frequency_unit_dropdown.get(),
                                                     phase_entry.get(),
                                                     voltage_entry.get(),
                                                     G_var) if action_type == "DEP" else None

        confirm_button = tk.Button(button_frame, text="Confirm", font=font_style, bg="lightgreen", width=10, command=command)
        confirm_button.grid(row=0, column=0, padx=10)

        cancel_button = tk.Button(button_frame, text="Cancel", font=font_style, bg="lightcoral", width=10, command=self.action_window.destroy)
        cancel_button.grid(row=0, column=1, padx=10)

    #########################
    # Confirm Create DEP Action
    #########################
    def confirm_create_action(self, action_type, action_name, folder_path, pattern_interval, timer_mode, loop_interval, loop_iterations, frequency, unit, phase, voltage, G_var):
        if action_type == "DEP":
            if action_name in [action.action_name for action in self.protocol.actions]:
                messagebox.showerror("Error", "Action name already exists.")
                self.action_window.focus_set()
                return
            
            if not os.path.exists(folder_path):
                messagebox.showerror("Error", "Folder path does not exist.")
                self.action_window.focus_set()
                return
            
            action = DEP_Action(action_name)
            action_pattern_interval = int(float(pattern_interval) * 1000)  # Convert to ms
            action_loop_interval = int(float(loop_interval) * 1000)  # Convert to ms
            action_frequency = float(frequency) * 1000 if unit == "kHz" else float(frequency) * 10**6 if unit == "MHz" else float(frequency)
            action.update_action(action_name, folder_path, action_pattern_interval, timer_mode, action_loop_interval, loop_iterations, action_frequency, phase, voltage)

            # # 執行讀取 pattern 的函數
            # if folder_path:
            #     action.read_pattern_from_folder(folder_path)

            self.protocol.add_action(action)
            self.create_step(action_name, 50-25, len(self.dep_steps) * 100)
            self.update_numbers()
            self.update_scrollbar()
            print(bcolors.OK + f"[Success] Successfully added {action_name} action." + bcolors.RESET)

        # check if the action window is open
        if self.action_window:
            self.action_window.destroy()  # 關閉視窗

    #########################
    # Create Protocol Step
    #########################
    def create_step(self, text, x, y):
        rect = self.create_rounded_rectangle(self.sub_canvas, x, y, x + 300, y + 50, fill="lightblue", tags="step")
        text_id = self.sub_canvas.create_text(x + 150, y + 25, text=text, anchor="center", tags="step_text", font=("Helvetica", 12, "bold"))
        
        # 將方框和文字綁定在一起，但不包含編號
        self.dep_steps.append((rect, text_id))
        self.update_arrows()
        # self.sub_canvas.tag_bind(rect, "<Enter>", lambda event: self.on_enter(text_id))

    #########################
    # Delete Action
    #########################
    def delete_action(self, G_var):
        # 確認當前是否有選中的 action
        print("Delete Action", self.selected_action)
        if self.selected_action:
            # 找到選中 action 的索引
            selected_action_index = self.dep_steps.index((self.selected_action, self.drag_data["text_id"]))
            action_name = self.protocol.actions[selected_action_index].action_name

            # 彈出確認刪除對話框
            confirm = messagebox.askyesno("Delete Action", f"Are you sure you want to delete the '{action_name}' action?")
            
            if confirm:
                # 從 protocol 中刪除對應的 action
                self.protocol.remove_action(selected_action_index)

                # 刪除畫布上的矩形和文字
                self.sub_canvas.delete(self.dep_steps[selected_action_index][0])  # 刪除 action 方框
                self.sub_canvas.delete(self.dep_steps[selected_action_index][1])  # 刪除 action 文字

                # 從 dep_steps 中刪除 action 對應的項目
                self.dep_steps.pop(selected_action_index)

                # 清除選擇狀態
                self.selected_action = None
                self.drag_data["item"] = None

                # 更新箭頭和編號
                self.update_arrows()
                self.update_numbers()
                self.update_scrollbar()
# =================================================================================================
# Run Action Functions (call the functions in Protocol.py)
# =================================================================================================
    #########################
    # Run Action
    #########################
    def call_run_selected_action(self, G_var: Global_Var):
        if self.selected_action: 
            selected_action_index = self.dep_steps.index((self.selected_action, self.drag_data["text_id"]))
            selected_action = self.protocol.actions[selected_action_index]
            self.stop_action(G_var)
            self.protocol.run_action(selected_action, G_var)
        else:
            print(bcolors.ERROR + "[Error] No action selected. Please select an action to run." + bcolors.RESET)
    
    #########################
    # Run Protocol
    #########################
    def call_run_protocol(self, G_var: Global_Var):
        self.stop_action(G_var)
        self.protocol.run_protocol(G_var)

    def call_run_protocol_with_loop(self, G_var: Global_Var):
        reset_func = lambda: self.stop_action(G_var)
        loop_protocol = LoopProtocolSetting(self.protocol, G_var, reset_func)

    def launch_console(self, G_var: Global_Var):
        console = ProtocolConsole(G_var)
        console.run()

    def run_script(self, G_var: Global_Var):
        script = ScriptRunner(self.root, G_var)
        script.run()
        
# =================================================================================================
# Action Properties Functions
# =================================================================================================
    #########################
    # Show Properties
    #########################
    # 屬性快捷鍵 "q" 或按鈕 "屬性"
    def show_properties(self, G_var):
        print("Show Properties, Action Name:", self.selected_action)
        if self.selected_action:  # 使用 selected_action 而不是 drag_data["item"]
            selected_action_index = self.dep_steps.index((self.selected_action, self.drag_data["text_id"]))
            selected_action = self.protocol.actions[selected_action_index]
            self.property_window = tk.Toplevel(self.root)
            self.property_window.title("Action Properties")

            # 設置視窗的統一字體
            font_style = ("Helvetica", 12)

            # 添加 LabelFrame 作為最外層框架
            property_frame = tk.LabelFrame(self.property_window, text="Property", font=("Helvetica", 14, "bold"))
            property_frame.pack(fill="both", expand="yes", padx=20, pady=20)

            # 使用 grid 布局來保持一致的對齊和間距
            tk.Label(property_frame, text="Action Name:", font=font_style).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            action_name_entry = tk.Entry(property_frame, font=font_style)
            action_name_entry.insert(0, selected_action.action_name)
            action_name_entry.grid(row=0, column=1, padx=10, pady=5)

            tk.Label(property_frame, text="Action Type:", font=font_style).grid(row=1, column=0, padx=10, pady=5, sticky="w")
            num_patterns_label = tk.Label(property_frame, text=selected_action.action_type, font=font_style)
            num_patterns_label.grid(row=1, column=1, padx=10, pady=5)

            tk.Label(property_frame, text="Folder Path:", font=font_style).grid(row=2, column=0, padx=10, pady=5, sticky="w")
            folder_path_entry = tk.Entry(property_frame, font=font_style)
            folder_path_entry.insert(0, selected_action.folder_path)
            folder_path_entry.grid(row=2, column=1, padx=10, pady=5)

            # 新增一個按鈕來讓使用者重新選擇資料夾
            browse_button = tk.Button(property_frame, text="Browse", font=font_style, command=lambda: self.open_dep_pattern_folder(folder_path_entry))
            browse_button.grid(row=2, column=2, padx=10, pady=5)

            tk.Label(property_frame, text="Number of Patterns:", font=font_style).grid(row=3, column=0, padx=10, pady=5, sticky="w")
            num_patterns_label = tk.Label(property_frame, text=str(selected_action.num_pattern), font=font_style)
            num_patterns_label.grid(row=3, column=1, padx=10, pady=5)

            # create pattern interval and loop iterations entry in the same row
            tk.Label(property_frame, text="Pattern Interval (s):", font=font_style).grid(row=4, column=0, padx=10, pady=5, sticky="w")
            pattern_interval_entry = tk.Entry(property_frame, font=font_style)
            pattern_interval_entry.insert(0, selected_action.pattern_interval / 1000)
            pattern_interval_entry.grid(row=4, column=1, padx=10, pady=5)
            pattern_interval_entry.focus_set()

            timer_mode_dropdown = ttk.Combobox(property_frame, values=["Correct", "Normal"], font=('Arial',10), width=8, state="readonly")
            timer_mode_dropdown.set(selected_action.timer_mode)
            timer_mode_dropdown.grid(row=4, column=2, padx=10, pady=5)
        
            tk.Label(property_frame, text="Loop Iterations (times):", font=font_style).grid(row=5, column=0, padx=10, pady=5, sticky="w")
            loop_iterations_entry = tk.Entry(property_frame, font=font_style)
            loop_iterations_entry.insert(0, selected_action.loop_iterations)
            loop_iterations_entry.grid(row=5, column=1, padx=10, pady=5)

            tk.Label(property_frame, text="Loop Interval (s):", font=font_style).grid(row=6, column=0, padx=10, pady=5, sticky="w")
            loop_interval_entry = tk.Entry(property_frame, font=font_style)
            loop_interval_entry.insert(0, selected_action.loop_interval / 1000)
            loop_interval_entry.grid(row=6, column=1, padx=10, pady=5)
                  
            #action_frequency entry (value) + dropdown menu (for unit)
            tk.Label(property_frame, text="Action Frequency:", font=font_style).grid(row=7, column=0, padx=10, pady=5, sticky="w")
            action_frequency_entry = tk.Entry(property_frame, font=font_style)            
            action_frequency_entry.grid(row=7, column=1, padx=10, pady=5)

            # Frequency Unit Dropdown
            frequency_unit_dropdown = ttk.Combobox(property_frame, values=["Hz", "kHz", "MHz"], font=font_style, width=6, state="readonly")
            frequency_unit_dropdown.set("MHz")
            frequency_unit_dropdown.grid(row=7, column=2, padx=10, pady=5)

            # Set the initial value of the dropdown menu based on the action frequency value 
            if selected_action.action_frequency < 1000:
                frequency_unit_dropdown.set("Hz")
                action_frequency_entry.insert(0, selected_action.action_frequency)
            elif selected_action.action_frequency < 1000000:
                frequency_unit_dropdown.set("kHz")
                action_frequency_entry.insert(0, selected_action.action_frequency / 1000)
            elif selected_action.action_frequency < 1000000000:
                frequency_unit_dropdown.set("MHz")
                action_frequency_entry.insert(0, selected_action.action_frequency / 1000000)

            #action_phase entry (value)
            tk.Label(property_frame, text="Action Phase (deg):", font=font_style).grid(row=8, column=0, padx=10, pady=5, sticky="w")
            action_phase_entry = tk.Entry(property_frame, font=font_style)
            action_phase_entry.insert(0, selected_action.action_phase)
            action_phase_entry.grid(row=8, column=1, padx=10, pady=5)

            #action_voltage entry (value) 
            tk.Label(property_frame, text="Action Voltage (Vpp):", font=font_style).grid(row=9, column=0, padx=10, pady=5, sticky="w")
            action_voltage_entry = tk.Entry(property_frame, font=font_style)
            action_voltage_entry.insert(0, selected_action.action_voltage)
            action_voltage_entry.grid(row=9, column=1, padx=10, pady=5)        


            # Preview and 確認與取消按鈕

            button_frame = tk.Frame(self.property_window)
            button_frame.pack(pady=20)

            preview_button = tk.Button(button_frame, text="Preview", font=font_style, bg="lightblue", width=10, command=lambda: self.preview_action(selected_action_index, G_var))
            preview_button.grid(row=0, column=0, padx=10)

            update_button = tk.Button(button_frame, text="Update", font=font_style, bg="lightgreen", width=10, command=lambda: self.update_action(selected_action_index, action_name_entry.get(), folder_path_entry.get(), pattern_interval_entry.get(), timer_mode_dropdown.get(), loop_interval_entry.get(), loop_iterations_entry.get(), action_frequency_entry.get(), frequency_unit_dropdown.get(), action_phase_entry.get(), action_voltage_entry.get(), G_var))
            update_button.grid(row=0, column=1, padx=10)

            cancel_button = tk.Button(button_frame, text="Cancel", font=font_style, bg="lightcoral", width=10, command=self.property_window.destroy)
            cancel_button.grid(row=0, column=2, padx=10)

    #########################
    # Preview Action
    #########################
    def preview_action(self, index, G_var: Global_Var):
        if G_var.is_running:
            messagebox.showwarning("Warning", "Please stop the current action before previewing a new action.")
            return
        
        selected_action = self.protocol.actions[index]
        if selected_action.num_pattern == 0:
            messagebox.showwarning("Warning", "No pattern found in the folder.")
            self.property_window.focus_set()
            return
        
        self.stop_action(G_var)
        print(bcolors.STATUS + f"[Info] Preview selected action: {selected_action.action_name}..." + bcolors.RESET)
        self.protocol.run_action(selected_action, G_var, preview=True)

    #########################
    # Update Action
    #########################
    def update_action(self, index, action_name, folder_path, pattern_interval, timer_mode, loop_interval, loop_iterations, frequency, unit, phase, voltage, G_var):
        # 更新 Action 參數
        action: Union[DEP_Action, CS_Action, Heating_Action] = self.protocol.actions[index]
        if action_name in [ac.action_name for ac in self.protocol.actions if action != ac]:
            messagebox.showerror("Error", "Action name already exists.")
            self.property_window.focus_set()
            return
        action_frequency = float(frequency) * 1000 if unit == "kHz" else float(frequency) * 1000000 if unit == "MHz" else float(frequency)
        pattern_interval = float(pattern_interval) * 1000
        loop_interval = float(loop_interval) * 1000
        action.update_action(action_name, folder_path, pattern_interval, timer_mode, loop_interval, loop_iterations, action_frequency, phase, voltage)
        
        # 更新顯示
        self.sub_canvas.itemconfig(self.dep_steps[index][1], text=action_name)

        self.property_window.destroy()  # 關閉屬性視窗
    

# =================================================================================================
# Protocal Event Functions
# =================================================================================================
    def create_rounded_rectangle(self, canvas: tk.Canvas, x1, y1, x2, y2, radius=20, **kwargs):
        points = [x1+radius, y1,
                x1+radius, y1,
                x2-radius, y1,
                x2-radius, y1,
                x2, y1,
                x2, y1+radius,
                x2, y1+radius,
                x2, y2-radius,
                x2, y2-radius,
                x2, y2,
                x2-radius, y2,
                x2-radius, y2,
                x1+radius, y2,
                x1+radius, y2,
                x1, y2,
                x1, y2-radius,
                x1, y2-radius,
                x1, y1+radius,
                x1, y1+radius,
                x1, y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)
    #########################
    # Double Click Event
    #########################
    # 新增處理雙擊事件的方法
    def on_double_click(self, event: tk.Event, G_var):
        # 判斷是否點擊在一個 action 方框上
        # item = self.sub_canvas.find_closest(event.x, event.y)

        # [Revised] 更精準定位
        absolute_y = self.sub_canvas.canvasy(event.y)
        item = self.sub_canvas.find_overlapping(event.x-1, absolute_y-1, event.x+1, absolute_y+1) 
        if item:
            for rect, text_id in self.dep_steps:
                if rect == item[0]:
                    self.drag_data["item"] = rect
                    self.drag_data["text_id"] = text_id
                    self.selected_action = rect  # 將選中的 action 設置為選擇的項目
                    self.show_properties(G_var)  # 觸發屬性視窗
                    break

        else:
            self.add_action("DEP", G_var)
    
    #########################
    # Click On Object Event
    #########################
    # 選擇 Action 框變色
    def on_start(self, event: tk.Event, right_click=False):
        # item = self.sub_canvas.find_closest(event.x, event.y)

        # [Revised] 即使點到文字也可以選中整個方框
        absolute_y = self.sub_canvas.canvasy(event.y)
        item = self.sub_canvas.find_overlapping(event.x-1, absolute_y-1, event.x+1, absolute_y+1) 
        is_action = False

        # 檢查是否點擊到了空白區域
        if item:
            for rect, text_id in self.dep_steps:
                if rect == item[0]:
                    # 如果之前有選中的 action，恢復顏色
                    if self.selected_action:
                        self.sub_canvas.itemconfig(self.selected_action, fill="lightblue")

                    # 設置當前選中的 action 並更改顏色
                    self.drag_data["item"] = rect
                    self.drag_data["text_id"] = text_id
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = absolute_y
                    self.drag_data["start_y"] = self.sub_canvas.coords(rect)[1]
                    self.sub_canvas.itemconfig(rect, fill="yellow")  # 選擇的 Action 變色
                    self.selected_action = rect  # 保存當前選中的 Action
                    is_action = True  # 標記為點擊到 Action
                    if right_click:
                        self.context_menu.post(event.x_root, event.y_root)  # 右鍵點擊時顯示右鍵菜單
                    break

        if self.selected_action is not None and not is_action and not right_click:  # 點擊到空白區域
            self.sub_canvas.itemconfig(self.selected_action, fill="lightblue")
            self.selected_action = None  # 清除選中狀態

    #########################
    # Hovered-over Event
    #########################
    def on_enter(self, text_id):
        text = self.sub_canvas.itemcget(text_id, "text")
        print(f"\rHovered over: {text}")
                    
# =================================================================================================
# Drop and Move Object Functions
# =================================================================================================
    #########################
    # Drop object Event
    #########################             
    def on_drop(self, event,G_var):
        if self.drag_data["item"]:
            for rect, text_id in self.dep_steps:
                if rect == self.drag_data["item"]:
                    coords = self.sub_canvas.coords(rect)
                    # 計算最近的對齊位置，保持 Y 軸垂直對齊
                    nearest_y = round((coords[1] - 100) / 100) * 100 + 100
                    # nearest_y = max(0, min(500, nearest_y))  # 限制 Y 軸範圍

                    # 計算 X 軸對齊：居中對齊 (X = 50 到 350)
                    center_x_left = 70-25
                    current_x_left = coords[0]
                    dx = center_x_left - current_x_left  # 計算 X 軸的移動量

                    # 計算 Y 軸的移動量
                    dy = nearest_y - coords[1]

                    # 使用 move 函數進行 X 和 Y 軸的移動
                    self.sub_canvas.move(rect, dx, dy)
                    self.sub_canvas.move(text_id, dx, dy)

                    start_y = self.drag_data["start_y"]
                    end_y = nearest_y
                    direction = "down" if end_y > start_y else "up"

                    # 檢查是否有重疊並移動重疊的元件
                    self.move_step(rect, direction)
                    self.update_arrows()  # 更新箭頭
                    break

            # 更新 Protocol 中的 actions 順序
            self.reorder_actions(G_var)

            # 更新編號和滾動條
            self.update_numbers()
            self.update_scrollbar()

            # 清除拖動數據
            self.drag_data["item"] = None


    #########################
    # Drag Object Event
    #########################
    def on_drag(self, event: tk.Event):
        absoulte_y = self.sub_canvas.canvasy(event.y)
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = absoulte_y - self.drag_data["y"]
            # 找到對應的方框、文字和編號
            for rect, text_id in self.dep_steps:
                if rect == self.drag_data["item"]:
                    coords = self.sub_canvas.coords(rect)
                    if 0 < coords[0] + dx < 400 and 0 < coords[1] + dy:
                        # 移動方框
                        self.sub_canvas.move(rect, dx, dy)
                        # 移動文字
                        self.sub_canvas.move(text_id, dx, dy)
                    break
            self.drag_data["x"] = event.x
            self.drag_data["y"] = absoulte_y

    #########################
    # Move Step
    #########################
    def move_step(self, item, direction):
        while True:
            overlapping_item = self.check_overlap(item)  # 檢查是否有重疊
            if overlapping_item:
                for rect, text_id in self.dep_steps:
                    if rect == overlapping_item:
                        coords = self.sub_canvas.coords(rect)
                        if direction == "down":
                            # 向上移動 100 像素，保持居中
                            new_y = max(coords[1] - 100, 100)  # 限制 Y 軸範圍
                            center_x_left = 70-25
                            current_x_left = coords[0]
                            dx = center_x_left - current_x_left  # 計算 X 軸移動量
                            self.sub_canvas.move(rect, dx, -100)  # 移動 X 和 Y
                            self.sub_canvas.move(text_id, dx, -100)
                        elif direction == "up":
                            # 向下移動 100 像素，保持居中
                            new_y = min(coords[1] + 100, 500)  # 限制 Y 軸範圍
                            center_x_left = 70-25
                            current_x_left = coords[0]
                            dx = center_x_left - current_x_left  # 計算 X 軸移動量
                            self.sub_canvas.move(rect, dx, 100)  # 移動 X 和 Y
                            self.sub_canvas.move(text_id, dx, 100)
                        item = rect  # 更新被移動的元件
                        break
            else:
                break
    #########################
    # Check Overlap
    #########################
    def check_overlap(self, item):
        # 取出 item 的左上角 (x1, y1) 和右下角 (x2, y2)
        coords1 = self.sub_canvas.coords(item)
        x1_item, y1_item = coords1[0], coords1[1]  # 左上角
        x2_item, y2_item = coords1[16], coords1[17]  # 右下角
        
        for rect, _ in self.dep_steps:
            if rect != item:  # 不检查自己和自己是否重叠
                coords2 = self.sub_canvas.coords(rect)
                x1_rect, y1_rect = coords2[0], coords2[1]  # 左上角
                x2_rect, y2_rect = coords2[16], coords2[17]  # 右下角
                
                # 检查两者是否重叠
                if not (x2_item <= x1_rect or  # item的右边 <= rect的左边
                        x1_item >= x2_rect or  # item的左边 >= rect的右边
                        y2_item <= y1_rect or  # item的下边 <= rect的上边
                        y1_item >= y2_rect):   # item的上边 >= rect的下边
                    return rect  # 如果重叠则返回重叠的rect
        return None  # 没有重叠则返回None
    
    #########################
    # Reorder Actions
    #########################
    def reorder_actions(self,G_var):
        """根據畫布中的順序重新排列 Protocol 中的 actions"""
        sorted_dep_steps = sorted(self.dep_steps, key=lambda step: self.sub_canvas.coords(step[0])[1])
        # 創建一個 name -> action 的映射表
        name_to_action = {action.action_name: action for action in self.protocol.actions}
        new_actions_order = []

        # 根據 sorted_dep_steps 重新排序 actions
        for rect, text_id in sorted_dep_steps:
            # 從文字 ID 中獲取 action 名稱
            action_name = self.sub_canvas.itemcget(text_id, "text")
            
            # 通過名稱找到對應的 action 並添加到新的順序
            if action_name in name_to_action:
                new_actions_order.append(name_to_action[action_name])
        # 更新 protocol 中的 actions 順序
        self.protocol.actions = new_actions_order
        print("Reordered Actions:", [action.action_name for action in self.protocol.actions])

    #########################
    # Update Protocol Step. Number
    #########################
    def update_numbers(self):
        # 先根據 Y 座標進行排序
        self.dep_steps.sort(key=lambda step: self.sub_canvas.coords(step[0])[1])

        # 刪除現有的數字
        self.sub_canvas.delete("step_number")

        # 重新根據順序顯示編號
        for i, (rect, text_id) in enumerate(self.dep_steps):
            coords = self.sub_canvas.coords(rect)
            # 調整編號的位置，使其遠離 Action 圓框
            self.sub_canvas.create_text(coords[0] - 30, coords[1] + 25, text=str(i + 1), font=("Helvetica", 10, "bold"), tags="step_number")

    #########################
    # Update Arrows
    #########################
    def update_arrows(self):
        # 刪除舊的箭頭符號
        for arrow in self.arrows:
            self.sub_canvas.delete(arrow)
        self.arrows.clear()

        # 按照 Y 座標排序 dep_steps，確保箭頭從上往下連接
        self.dep_steps.sort(key=lambda step: self.sub_canvas.coords(step[0])[1])

        # 在每個方塊之間畫出箭頭
        for i in range(len(self.dep_steps) - 1):
            # 取第一個和最後一個點來模擬 x1, y1 和 x2, y2
            coords1 = self.sub_canvas.coords(self.dep_steps[i][0])
            coords2 = self.sub_canvas.coords(self.dep_steps[i + 1][0])

            # 如果是多邊形，coords 可能有超過 4 個座標，僅取需要的座標
            x1, y1 = coords1[0], coords1[1]  # 多邊形的左上角
            x3, y3 = coords2[0], coords2[1]  # 下一個多邊形的左上角
            
            arrow = self.sub_canvas.create_line(x1 + 125, y1 + 50, x3 + 125, y3, arrow=tk.LAST)
            
            self.arrows.append(arrow)

    #########################
    # Update Scrollbar
    #########################
    def update_scrollbar(self):
        self.sub_canvas.config(scrollregion=self.sub_canvas.bbox("all"))

    #########################
    # Browse Folder
    #########################
    def open_dep_pattern_folder(self, folder_path_entry: tk.Entry):
        """
        Opens a folder dialog for selecting the DEP pattern folder.
        Returns the relative path to the selected folder.
        If no folder is selected, returns None.
        """
        # Set the default directory to './pattern/'
        default_dir = './pattern/'
        print("Default Directory:", default_dir)
        # Ensure the default directory exists
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)

        # Open the folder dialog and get the absolute path
        folder_path = filedialog.askdirectory(initialdir=default_dir, title="Select DEP Pattern Folder")

        if folder_path:
            # Convert the absolute path to a relative path
            relative_path = os.path.relpath(folder_path, start=os.getcwd())
            relative_path = relative_path.replace("\\", "/")
            # add ./ to the relative path
            relative_path = "./" + relative_path
            folder_path_entry.delete(0, tk.END)
            folder_path_entry.insert(0, relative_path)
            folder_path_entry.focus_set()
            return relative_path
        else:
            folder_path_entry.focus_set()
            return None  # Return None if no folder is selected

    
