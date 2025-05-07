# ========================================================
# Project:  BioFPGAG-G6-python
# File:     Action.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================

from src.header import *
from src.Chip import *
from src.AD2 import *
from typing import Union
#====================================================================================================
# Action Class
#  - Heating_Action
#  - CS_Action
#  - DEP_Action
# Action Must have the following methods:
#  - run_action()
#  - update_action()
#  - print_action()
#  - get_action_label()
#====================================================================================================
class Action:
    def __init__(self, action_name, action_type):
        self.action_name = action_name
        self.action_type = action_type

    def run_action(self):
        raise NotImplementedError("Subclasses must implement run_action")
    
    def update_action(self):
        raise NotImplementedError("Subclasses must implement update_action")

    def print_action(self):
        raise NotImplementedError("Subclasses must implement print_action")
    
    def get_action_label(self):
        raise NotImplementedError("Subclasses must implement get_action_label")

class Heating_Action(Action):
    def __init__(self, action_name, action_type="Heating", temperature=25):
        super().__init__(action_name, action_type)
        self.enable = False
        self.temperature = temperature
        

    def print_action(self):
        print(f"Heating Action - Name: {self.action_name}, Temperature: {self.temperature}°C")

    def get_action_label(self):
        if self.enable:
            #string = action name remove _Heating 
            string =  self.action_name.replace("_Heating","")
            string += f"\n {self.temperature}°C"
            return string
        else:
            #string = action name remove _Heating 
            string =  self.action_name.replace("_Heating","")
            string += f"\nHeat Off"
            return string
    
    def update_action(self, action_name, temperature):
        self.action_name = action_name
        self.temperature = temperature
    
    def run_action(self):
        print(f"Running Heating Action: {self.action_name} at {self.temperature}°C")



class CS_Action(Action):
    def __init__(self, action_name, action_type="CS"):
        super().__init__(action_name, action_type)
        self.enable = False
        self.DoAfterNumDEPActions = 5
        self.MultipleSamplingTimes = 1
        self.threshold = 16
        self.DPDG = {"from": 0, "step": 1, "to": 4000}
        self.DTC = {"from": 5600, "step": 10, "to": 7000}
        self.MODE = "DPDG"
        self.vctrl = 0


    def print_action(self):
        print(f"CS Action - Name: {self.action_name}")

    def get_action_label(self):
        if self.enable:
            #string = action name remove _CS 
            string =  self.action_name.replace("_CS","")
            string += f"\n {self.MODE}"
            return string
        else:
            #string = action name remove _CS 
            string =  self.action_name.replace("_CS","")
            string += f"\n  CS Off"
            return string

    def update_action(self, action_name):
        self.action_name = action_name

    def run_action(self):
        print(f"Running CS Action: {self.action_name}")
    
class DEP_Action(Action):
    def __init__(self, action_name, action_type="DEP"):
        super().__init__(action_name, action_type)
        self.PatternSeries = []
        self.action_frequency = 5000000 # 5MHz
        self.action_phase = 180
        self.action_voltage = 1.8
        self.num_pattern = 0
        self.pattern_interval = 500
        self.loop_interval = 0
        self.loop_iterations = 1
        self.folder_path = "."
        self.update_image_callback = None  # 確保有這個屬性
        self.golden_time = 0
        self.timer_mode = ''  # 'Correct' or 'Normal'

    def copy(self):
        new_action = DEP_Action(self.action_name)
        new_action.PatternSeries = self.PatternSeries.copy()
        new_action.action_frequency = self.action_frequency
        new_action.action_phase = self.action_phase
        new_action.action_voltage = self.action_voltage
        new_action.num_pattern = self.num_pattern
        new_action.pattern_interval = self.pattern_interval
        new_action.loop_interval = self.loop_interval
        new_action.loop_iterations = self.loop_iterations
        new_action.folder_path = self.folder_path
        new_action.update_image_callback = self.update_image_callback
        new_action.golden_time = self.golden_time
        new_action.timer_mode = self.timer_mode
        return new_action
    
    def get_golden_time(self, cur_pattern_index, cur_iteration):
        if cur_pattern_index == self.num_pattern - 1:
            return (self.pattern_interval * len(self.PatternSeries) + self.loop_interval) * (cur_iteration + 1)
        else:
            return (self.pattern_interval * len(self.PatternSeries) + self.loop_interval) * (cur_iteration) + self.pattern_interval * (cur_pattern_index + 1)
        
    def get_total_golden_time(self):
        return self.get_golden_time(self.num_pattern - 1, self.loop_iterations - 1)
    
    def add_zero_pattern(self):
        self.PatternSeries.append(np.zeros((128, 128), dtype=bool))
        self.num_pattern += 1

    def read_pattern_from_folder(self, folder_path):
        if os.path.exists(folder_path):
            self.folder_path = folder_path
            # [Revised] Clear all patterns before reading new patterns
            self.PatternSeries.clear()
            # Get all files with .csv extension
            files = [f for f in os.listdir(self.folder_path) if f.endswith(".csv")]
            
            # Extract numbers from filenames using regex
            file_tuples = []
            for file in files:
                match = re.search(r'(\d+)', file)  # Look for numeric parts in the filename
                if match:
                    number = int(match.group(1))  # Extract the number
                    file_tuples.append((number, file))
                else:
                    print(bcolors.WARNING + f"[Warning] Skipping file without number: {file}" + bcolors.RESET)
            
            # Sort files based on extracted numbers
            file_tuples.sort(key=lambda x: x[0])
            sorted_files = [t[1] for t in file_tuples]

            self.num_pattern = len(sorted_files)
            print(bcolors.STATUS + f"Reading {self.num_pattern} pattern files from {self.folder_path}" + bcolors.RESET)
            if self.num_pattern == 0:
                print(bcolors.ERROR + f"[Error] No valid pattern files found in {self.folder_path}." + bcolors.RESET)
                return
            
            if self.num_pattern > 100:
                print(bcolors.WARNING + f"[Warning] {self.num_pattern} patterns found in {self.folder_path}. Loading all patterns may take a long time." + bcolors.RESET)
                if not messagebox.askyesno("Load Patterns", "There are more than 100 patterns in the folder. Do you want to load all patterns?"):
                    return

            for file in sorted_files:
                # print(file)
                file_path = os.path.join(self.folder_path, file)
                pattern = np.genfromtxt(file_path, delimiter=',', dtype=int)
                pattern = pattern.astype(bool)
                if pattern.shape == (128, 128):
                    self.PatternSeries.append(pattern)
                else:
                    print(bcolors.ERROR + f"[Error] File {file} does not match the required 128x128 format." + bcolors.RESET)
                    self.PatternSeries.append(pattern)

            print(bcolors.OK + f"[Success] Successfully read {self.num_pattern} pattern files from {self.folder_path}." + bcolors.RESET)
        else:
            messagebox.showerror("Error", "Folder path does not exist.\n\nThe original patterns will be used.")
            print(bcolors.ERROR + f"[Error] Folder {self.folder_path} does not exist." + bcolors.RESET)
        
    def ad2_set_wave_parameters(self, G_var: Global_Var):
        if G_var.ad2_enable:
            G_var.ad2.set_wave_parameters(self.action_frequency, self.action_phase, self.action_voltage)
        G_var.dragdrop_app.update_AD2_status_frame(True, self.action_frequency, self.action_phase, self.action_voltage)
        
    
    def run_action(self, G_var: Global_Var, window: tk.Toplevel, callback=None, iteration=0, pattern_index=0, start_time_at_first=0, preview=False, time_offset=0):
        pattern_start_time = time.time()  # 僅顯示用，不參與時間計算

        if iteration == self.loop_iterations and pattern_index == 0 or self.num_pattern == 0:
            if not preview:
                G_var.dragdrop_app.update_DEP_time_stamp()
                
            print(f"[{'Preview' if preview else 'Run'}] {self.action_name} finished after {self.loop_iterations} iterations.")
            if callback:
                callback()
            return
        
        if G_var.is_stopped:  # 理論上不會進入這個條件
            print(f"[{'Preview' if preview else 'Run'}] {self.action_name} stopped.")
            return  
        
        if G_var.is_paused:
            G_var.pause_sec += 1
            print(f"[{'Preview' if preview else 'Run'}] {self.action_name} is paused.", G_var.pause_sec)
            G_var.pending_id = window.after(1000, lambda: self.run_action(G_var, window, callback, iteration, pattern_index, start_time_at_first, preview=preview, time_offset=time_offset))  # 1000ms 檢查一次是否恢復
            return

        print(f"[{'Preview' if preview else 'Run'}] Action: {self.action_name}, Iteration: {iteration + 1}, Pattern: {pattern_index + 1}")
        
        # 發送當前的 pattern
        if not preview:
            G_var.dragdrop_app.update_DEP_status_frame(self.action_name, iteration + 1, self.loop_iterations, pattern_index + 1, self.num_pattern, self.pattern_interval)
            self.send_pattern(self.PatternSeries[pattern_index])
            
        # print(f"Sending pattern {pattern_index + 1}...")
        status_text = f"Protocol {G_var.protocol.name}, Action {self.action_name}, Iteration {iteration + 1}, Pattern {pattern_index+1}"
        update_status(G_var,status_text)
        try:
            Func_update_pattern_image(self.PatternSeries[pattern_index], G_var)
        except tk.TclError:
            messagebox.showerror("Error", "The display window has been closed. Please reopen the display window.")
            G_var.is_stopped = True
            return

        next_pattern_index = pattern_index + 1 if pattern_index < len(self.PatternSeries) - 1 else 0
        next_iteration = iteration + 1 if pattern_index == len(self.PatternSeries) - 1 else iteration

        # 調整時間
        if self.timer_mode == 'Correct':
            golden_time = self.get_golden_time(pattern_index, iteration) + (time_offset + G_var.pause_sec) * 1000  # 預計延遲時間 (ms)
            all_elapsed_time = (time.time() - start_time_at_first) * 1000  # 已經執行時間 (ms)
        else:
            golden_time = self.pattern_interval + (self.loop_interval if next_pattern_index == 0 else 0)  # 預計延遲時間 (ms)
            all_elapsed_time = (time.time() - pattern_start_time) * 1000  # 已經執行時間 (ms)

        real_delay_time = golden_time - all_elapsed_time # 實際應延遲時間
        if real_delay_time < 0:
            real_delay_time = 0

        G_var.pending_id = window.after(int(real_delay_time), lambda: self.run_action(G_var, window, callback, next_iteration, next_pattern_index, start_time_at_first, preview=preview, time_offset=time_offset))
        print(f"[{'Preview' if preview else 'Run'}] Finished pattern {pattern_index + 1} with elapsed time {(time.time() - pattern_start_time) * 1000:.2f} ms, waiting for {real_delay_time:.2f} ms to send next pattern...")

    def send_pattern(self, pat):
        # check if RASPBERRY_PI_IP defined
        if not RPI_ON:
            print(bcolors.ERROR + "RASPBERRY_PI_IP is not defined in header.py" + bcolors.RESET)
            return
        # reset_chip_on_pi()
        send_pattern_to_pi(pat)
        # print(f"Sending pattern... {self.action_name}")
        # print(f"Pattern: {np.array2string(pat, max_line_width=180)}")
        # 每次發送 pattern 時調用回調函數來更新顯示
        # update_pattern_image(pat,G_var)

    def wait_non_blocking(self, milliseconds):
        start = time.time()
        while (time.time() - start) * 1000 < milliseconds:
            time.sleep(0.01)

    def print_action(self):
        print(bcolors.OK + "=" * 50 + bcolors.RESET)
        print(bcolors.RESET + f"Action Name: {self.action_name}, Type: {self.action_type}" + bcolors.RESET)
        print(bcolors.RESET + f"Number of Patterns: {self.num_pattern}, Folder Path: {self.folder_path}" + bcolors.RESET)
        print(bcolors.RESET + f"Pattern Interval: {self.pattern_interval} ms, Loop Interval: {self.loop_interval} ms, Loop Iterations: {self.loop_iterations}" + bcolors.RESET)
        print(bcolors.RESET + f"Golden Time: {(self.get_total_golden_time()/1000)} s, Timer Mode: {self.timer_mode}" + bcolors.RESET)
        print(bcolors.RESET + f"Action Frequency: {self.action_frequency} Hz, Action Phase: {self.action_phase}, Action Voltage: {self.action_voltage} V" + bcolors.RESET)
        print(bcolors.OK + "=" * 50 + bcolors.RESET)
        # for idx, pattern in enumerate(self.PatternSeries):
        #     print(f"Pattern {idx}: {np.array2string(pattern, max_line_width=180)}")
    
    def update_action(self, action_name, folder_path, pattern_interval, timer_mode, loop_interval, loop_iterations, action_frequency, action_phase, action_voltage):
        if folder_path != self.folder_path:
            self.read_pattern_from_folder(folder_path)
        self.action_name = action_name
        # self.folder_path = folder_path    # [Revised] Folder path is updated in read_pattern_from_folder()
        self.pattern_interval = int(pattern_interval)  # ms
        self.timer_mode = timer_mode
        self.loop_interval = int(loop_interval)  # ms
        self.loop_iterations = int(loop_iterations)
        self.action_frequency = float(action_frequency)
        self.action_phase = float(action_phase)
        self.action_voltage = float(action_voltage)
        print( bcolors.STATUS + f"Action {self.action_name} updated." + bcolors.RESET)
        # self.print_action()
    
    def get_action_label(self):
        return f"{self.action_name}"
        # return f"{self.action_name} {self.num_pattern} patterns \n {self.loop_iterations} times, {self.loop_interval} ms interval"