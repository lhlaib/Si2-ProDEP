# ========================================================
# Project:  BioFPGAG-G6-python
# File:     Protocol.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================

# ========================================================
# Protocol Class
#  - Protocol
# Protocol Must have the following methods:
#  - add_action()
#  - remove_action()
#  - run_protocol()
#  - print_protocol()
#  - save_protocol_to_json()
#  - load_protocol_from_json()
# Protocol stores with JSON format in bio-protocal folder
# ========================================================

from src.header import *
from src.Action import *
from src.Display import DualDisplayApp
# from src.console import *
import re 
class Protocol:
    def __init__(self, G_var):
        self.actions: list[DEP_Action] = []
        self.heating_actions: list[Heating_Action] = []
        self.cs_actions: list[CS_Action] = []
        self.name = "Default Name"
        self.version = "1.0"
        self.dual_display_app = DualDisplayApp(G_var)
        self.console = None
        self.launch_time_stamp = -1
        self.pending_id = ''

    def reset_protocol(self, G_var):
        self.actions.clear()
        self.heating_actions.clear()
        self.cs_actions.clear()
        self.dual_display_app.root.destroy()
        self.open_new_dual_display(G_var)
    
    def open_new_dual_display(self,G_var: Global_Var):
        # [Bug Fixed] 處理 memory leak 導致無法正確 refernce 的問題
        del self.dual_display_app
        self.dual_display_app = DualDisplayApp(G_var)
        G_var.display_window = self.dual_display_app.root
        # To do: open new dual display window with old settings

    def add_action(self, action):
        # 根據 action 的類型將其添加到對應的列表中
        if isinstance(action, DEP_Action):
            self.actions.append(action)  # DEP Action 加入 actions 列表
        elif isinstance(action, Heating_Action):
            self.heating_actions.append(action)  # Heating Action 加入 heating_actions 列表
        elif isinstance(action, CS_Action):
            self.cs_actions.append(action)  # CS Action 加入 cs_actions 列表
        else:
            print(f"Unknown action type: {type(action)}")

    def remove_action(self, index):
        if 0 <= index < len(self.actions):
            del self.actions[index]

    def run_action(self, action: DEP_Action, G_var: Global_Var, preview=False):
        self.launch_time_stamp = time.time()
        G_var.is_running = not preview
        G_var.is_stopped = False  # 重置停止標誌
        def run_next_action(index):
            if index < 1:
                action.ad2_set_wave_parameters(G_var)
                action.run_action(G_var, G_var.display_window, callback=lambda : run_next_action(index + 1),
                                  iteration=0, pattern_index=0, start_time_at_first=self.launch_time_stamp, preview=preview)
            else:
                G_var.is_stopped = True
                print( bcolors.STATUS + f"[Info] Selected action {action.action_name} execution finished." + bcolors.RESET)
                print(f"Total time: {time.time() - self.launch_time_stamp:.2f} seconds")
                status_text = f"Action {action.action_name} execution finished."
                update_status(G_var,status_text)
                return
            
        # 從第一個 action 開始
        run_next_action(0)


    def run_protocol(self, G_var: Global_Var, extern_protocol: Optional[list[DEP_Action]]=None):
        """
        非同步運行 Protocol，確保每個 action 完成後再運行下一個 action
        """
        self.launch_time_stamp = time.time()
        G_var.is_running = True
        G_var.is_stopped = False  # 重置停止標誌
        def run_next_action(index, time_offset, action_list: list[DEP_Action]):
            if index < len(action_list):
                action: DEP_Action = action_list[index]
                action.ad2_set_wave_parameters(G_var)
                next_time_offset = time_offset + action.get_total_golden_time() / 1000 
                action.run_action(G_var, G_var.display_window, callback=lambda : run_next_action(index + 1, next_time_offset, action_list),
                                  iteration=0, pattern_index=0, start_time_at_first=self.launch_time_stamp, time_offset=time_offset)
            else:
                G_var.is_stopped = True
                print("Protocol execution finished.")
                print(f"Total time: {time.time() - self.launch_time_stamp:.2f} seconds")
                status_text = f"Protocol {self.name} execution finished."
                update_status(G_var,status_text)

        # 從第一個 action 開始，並將時間偏移重設為 0
        run_next_action(0, 0, self.actions if extern_protocol is None else extern_protocol)

    def run_protocol_with_loop(self, G_var: Global_Var, loop_protocols: int, frequencies: list[float], sweep_actions_index: list[int]):
        loop_action_list = []
        for i in range(loop_protocols):
            for j, action in enumerate(self.actions):
                new_action = action.copy()
                if j in sweep_actions_index:
                    new_action.action_frequency = frequencies[i]
                loop_action_list.append(new_action)

        self.run_protocol(G_var, extern_protocol=loop_action_list)
        for action in loop_action_list:
            del action
    
    def print_protocol(self, G_var: Global_Var):
        print(bcolors.OK + "=" * 50 + bcolors.RESET)
        print(bcolors.OK + f"Protocol Name: {self.name}, Version: {self.version}" + bcolors.RESET)
        for action in self.actions:
            action.print_action()
        print(bcolors.OK + "=" * 50 + bcolors.RESET)

        sub_screen = tk.Toplevel()
        sub_screen.title("Protocol Information")
        tree = ttk.Treeview(sub_screen)
        tree["columns"] = ("action_name", "total_golden_time", "ad2_settings")
        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("action_name", anchor=tk.W, width=150)
        tree.column("total_golden_time", anchor=tk.W, width=150)
        tree.column("ad2_settings", anchor=tk.W, width=150)
        tree.heading("#0", text="", anchor=tk.W)
        tree.heading("action_name", text="Action Name", anchor=tk.W)
        tree.heading("total_golden_time", text="Total Golden Time (s)", anchor=tk.W)
        tree.heading("ad2_settings", text="AD2 Frequency (Hz)", anchor=tk.W)
        for i, action in enumerate(self.actions):
            values = action.action_name, action.get_total_golden_time()/1000, format_number(action.action_frequency)
            tree.insert("", i, text="", values=values)
        tree.pack(expand=tk.YES, fill=tk.BOTH)
        scroll = ttk.Scrollbar(sub_screen, orient=tk.VERTICAL, command=tree.yview)
        scroll.place(relx=1, relheight=1, anchor=tk.NE)
        tree.config(yscrollcommand=scroll.set)


    def save_protocol_to_json(self, filename):
        data = {
            "name": self.name,  # 将 name 和 version 加入到保存的 JSON 中
            "version": self.version,
            "actions": [],
            "ai_detection": []
        }
        # Create a helper function to handle action serialization
        def serialize_action(action):
            action_data = {
                "action_name": action.action_name,
                "action_type": action.action_type
            }
            if isinstance(action, DEP_Action):
                action_data.update({
                    "pattern_interval": action.pattern_interval,
                    "timer_mode": action.timer_mode,
                    "loop_interval": action.loop_interval,
                    "loop_iterations": action.loop_iterations,
                    "folder_path": action.folder_path,
                    "action_frequency": action.action_frequency,
                    "action_phase": action.action_phase,
                    "action_voltage": action.action_voltage
                })
            elif isinstance(action, Heating_Action):
                action_data.update({
                    "enable": action.enable,
                    "temperature": action.temperature
                })
            elif isinstance(action, CS_Action):
                action_data.update({
                    "enable": action.enable,
                    "DoAfterNumDEPActions": action.DoAfterNumDEPActions,
                    "MultipleSamplingTimes": action.MultipleSamplingTimes,
                    "threshold": action.threshold,
                    "DPDG": action.DPDG,
                    "DTC": action.DTC,
                    "MODE": action.MODE,
                    "vctrl": action.vctrl
                })
            return action_data

        # Iterate through all types of actions
        for action in self.actions:
            data["actions"].append(serialize_action(action))

        for action in self.heating_actions:
            data["actions"].append(serialize_action(action))

        for action in self.cs_actions:
            data["actions"].append(serialize_action(action))
        
        ai_detection_data = {
                "camera_adjust": {
                    "cam_x": self.dual_display_app.cam_x,
                    "cam_y": self.dual_display_app.cam_y,
                    "cam_width": self.dual_display_app.cam_width,
                    "cam_height": self.dual_display_app.cam_height
                },
                "calibration": {
                    "show_cross": self.dual_display_app.show_cross,
                    "top_left_cross_x": self.dual_display_app.top_left_cross_x,
                    "top_left_cross_y": self.dual_display_app.top_left_cross_y,
                    "bottom_right_cross_x": self.dual_display_app.bottom_right_cross_x,
                    "bottom_right_cross_y": self.dual_display_app.bottom_right_cross_y
                },
                "detection": {
                    "confidence": self.dual_display_app.confidence,
                    "overlap": self.dual_display_app.overlap,
                    "show_detect": self.dual_display_app.show_detect
                },
                "pattern_gen": {
                    "thickness": self.dual_display_app.thickness,
                    "hollow": self.dual_display_app.hollow
                }
            }
        
        data["ai_detection"].append(ai_detection_data)
        # Save the protocol to a JSON file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Protocol saved to {filename}")
       


    def load_protocol_from_json(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        print(f"Loading protocol from {filename}")
        # Update Protocol Name and Version
        self.name = data.get("name", "Default Name")
        self.version = data.get("version", "1.0")

        self.actions.clear()
        self.heating_actions.clear()
        self.cs_actions.clear()
        for action_data in data["actions"]:
            action_type = action_data["action_type"]

            if action_type == "DEP":
                action = DEP_Action(action_data["action_name"])
                action.pattern_interval = action_data.get("pattern_interval", 1000)
                action.loop_interval = action_data.get("loop_interval", 0)
                action.loop_iterations = action_data.get("loop_iterations", 1)
                action.folder_path = action_data.get("folder_path", "")
                action.action_frequency = action_data.get("action_frequency", 5000000)
                action.action_phase = action_data.get("action_phase", 180)
                action.action_voltage = action_data.get("action_voltage", 1.8)
                action.timer_mode = action_data.get("timer_mode", "Correct")
                action.read_pattern_from_folder(action.folder_path)
                self.actions.append(action)

            elif action_type == "Heating":
                action = Heating_Action(action_data["action_name"])
                action.enable = action_data.get("enable", False)
                action.temperature = action_data.get("temperature", 25)
                self.heating_actions.append(action)

            elif action_type == "CS":
                action = CS_Action(action_data["action_name"])
                action.enable = action_data.get("enable", False)
                action.DoAfterNumDEPActions = action_data.get("DoAfterNumDEPActions", 5)
                action.MultipleSamplingTimes = action_data.get("MultipleSamplingTimes", 1)
                action.threshold = action_data.get("threshold", 16)
                action.DPDG = action_data.get("DPDG", {"from": 0, "step": 1, "to": 4000})
                action.DTC = action_data.get("DTC", {"from": 5600, "step": 10, "to": 7000})
                action.MODE = action_data.get("MODE", "DPDG")
                action.vctrl = action_data.get("vctrl", 0)
                self.cs_actions.append(action)

            else:
                print(f"Unknown action type: {action_type}")
                continue  # Skip any unknown action types
        
        # Load AI Detection Data
        ai_detection_data = data["ai_detection"][0]
        self.dual_display_app.cam_x = ai_detection_data["camera_adjust"]["cam_x"]
        self.dual_display_app.cam_y = ai_detection_data["camera_adjust"]["cam_y"]
        self.dual_display_app.cam_width = ai_detection_data["camera_adjust"]["cam_width"]
        self.dual_display_app.cam_height = ai_detection_data["camera_adjust"]["cam_height"]

        self.dual_display_app.show_cross = ai_detection_data["calibration"]["show_cross"]
        self.dual_display_app.top_left_cross_x = ai_detection_data["calibration"]["top_left_cross_x"]
        self.dual_display_app.top_left_cross_y = ai_detection_data["calibration"]["top_left_cross_y"]
        self.dual_display_app.bottom_right_cross_x = ai_detection_data["calibration"]["bottom_right_cross_x"]
        self.dual_display_app.bottom_right_cross_y = ai_detection_data["calibration"]["bottom_right_cross_y"]

        self.dual_display_app.confidence = ai_detection_data["detection"]["confidence"]
        self.dual_display_app.overlap = ai_detection_data["detection"]["overlap"]
        self.dual_display_app.show_detect = ai_detection_data["detection"]["show_detect"]

        self.dual_display_app.thickness = ai_detection_data["pattern_gen"]["thickness"]
        self.dual_display_app.hollow = ai_detection_data["pattern_gen"]["hollow"]

        print(bcolors.OK + f"Protocol {self.name} loaded successfully." + bcolors.RESET)