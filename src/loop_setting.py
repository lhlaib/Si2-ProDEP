import tkinter as tk
from tkinter import ttk, messagebox
from src.Protocol import *


class LoopProtocolSetting: 
    def __init__(self, protocol: Protocol, G_var: Global_Var, reset_func):
        self.protocol = protocol
        self.loop_window = tk.Toplevel()
        self.loop_window.title("Run Protocol with Loop")
        self.loop_window.grab_set()
        font_style = ("Arial", 11)
        self.reset_gui_func = reset_func
        
        loop_choice_frame = tk.Frame(self.loop_window)
        loop_choice_frame.pack(fill="both", expand="yes", padx=20, pady=0)
        
        tk.Label(loop_choice_frame, text="Loop Iterations for Protocol:", font=font_style).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.protocol_loop_entry = ttk.Spinbox(loop_choice_frame, from_=2, to=100, increment=1, font=font_style)
        self.protocol_loop_entry.grid(row=0, column=1, padx=10, pady=0)
        self.protocol_loop_entry.focus_set()
        self.protocol_loop_entry.insert(0, "2")

        # Sweep Frequency
        tk.Label(loop_choice_frame, text="Sweep Frequency:", font=font_style).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.sweep_frequency_var = tk.StringVar(value="Disable")
        sweep_frequency_options = ["Disable", "Log", "Linear", "Custom"]
        sweep_frequency_menu = ttk.Combobox(loop_choice_frame, values=sweep_frequency_options, textvariable=self.sweep_frequency_var, state="readonly", font=font_style)
        sweep_frequency_menu.grid(row=1, column=1, padx=10, pady=5)

        # Dynamic parameter frame for frequency settings
        self.parameter_frame = tk.Frame(loop_choice_frame)
        
        # Bind mode change to update parameters
        self.sweep_frequency_var.trace("w", self.update_parameters)

        # Action List with Selection for Sweep
        self.action_label = tk.Label(loop_choice_frame, text="Select Actions for Sweep:", font=font_style)
        self.action_frame = tk.Frame(loop_choice_frame)
        self.action_vars = {}
        for action in self.protocol.actions:
            var = tk.BooleanVar(value=False)
            self.action_vars[action.action_name] = var
            tk.Checkbutton(self.action_frame, text=action.action_name, variable=var, font=font_style).pack(anchor="w")
        
        button_frame = tk.Frame(self.loop_window)
        button_frame.pack(pady=20)
        exe_loop_button = ttk.Button(button_frame, text="Confirm", width=10, command=lambda : self.confirm_loop(G_var))
        exe_loop_button.grid(row=0, column=0, padx=10)
        cancel_button = ttk.Button(button_frame, text="Cancel", width=10, command=self.loop_window.destroy)
        cancel_button.grid(row=0, column=1, padx=10)

    # Function to update parameters based on sweep mode
    def update_parameters(self, *args):
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()

        font_style = ("Arial", 11)
        mode = self.sweep_frequency_var.get()
        if mode == "Disable":
            self.action_label.grid_remove()
            self.action_frame.grid_remove()
            self.parameter_frame.grid_remove()
            return
        
        self.parameter_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        if mode == "Log" or mode == "Linear":
            self.num_freq_entry = ttk.Entry(self.parameter_frame, font=font_style)
            tk.Label(self.parameter_frame, text="Number of frequencies:", font=font_style).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.num_freq_entry.grid(row=0, column=1, padx=5, pady=5)
            self.num_freq_entry.insert(0, self.protocol_loop_entry.get())
            
            self.log_start_entry = ttk.Entry(self.parameter_frame, font=font_style)
            self.log_start_unit = ttk.Combobox(self.parameter_frame, values=["MHz", "kHz", "Hz"], state="readonly", font=font_style, width=6)
            tk.Label(self.parameter_frame, text="Start Frequency:", font=font_style).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.log_start_entry.grid(row=1, column=1, padx=5, pady=5)
            self.log_start_entry.insert(0, "1")
            self.log_start_unit.grid(row=1, column=2, padx=5, pady=5)
            self.log_start_unit.set("MHz") 

            self.log_end_entry = ttk.Entry(self.parameter_frame, font=font_style)
            self.log_end_unit = ttk.Combobox(self.parameter_frame, values=["MHz", "kHz", "Hz"], state="readonly", font=font_style, width=6)
            tk.Label(self.parameter_frame, text="End Frequency:", font=font_style).grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.log_end_entry.grid(row=2, column=1, padx=5, pady=5)
            self.log_end_entry.insert(0, "100")
            self.log_end_unit.grid(row=2, column=2, padx=5, pady=5)
            self.log_end_unit.set("kHz")  

        elif mode == "Custom":
            tk.Label(self.parameter_frame, text="Custom Frequency List (Hz):", font=font_style).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.custom_freq_entry = ttk.Entry(self.parameter_frame, font=font_style)
            self.custom_freq_entry.grid(row=0, column=1, padx=5, pady=5)
            self.custom_freq_entry.insert(0, "1M, 2M, 3M")

        self.action_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        self.action_label.grid(row=3, column=0, padx=10, pady=10, sticky="nw")

    def confirm_loop(self, G_var):
        multiplier = {'kHz': 1e3, 'Hz': 1, 'MHz': 1e6, 'k': 1e3, 'M': 1e6, 'K': 1e3, 'KHz': 1e3}  
        loop_iterations = int(self.protocol_loop_entry.get())
        if loop_iterations <= 1:
            messagebox.showerror("Error", "Loop iterations must be greater than 1.")
            self.protocol_loop_entry.focus_set()
            return
        
        sweep_mode = self.sweep_frequency_var.get()
        frequencies = []

        if sweep_mode == "Log" or sweep_mode == "Linear":
            start_freq = float(eval(self.log_start_entry.get())) * multiplier[self.log_start_unit.get()]
            end_freq = float(eval(self.log_end_entry.get())) * multiplier[self.log_end_unit.get()]
            num_freq = int(self.num_freq_entry.get())
            if loop_iterations % num_freq != 0:
                messagebox.showerror("Error", "Loop iterations must be divisible by the number of frequencies.")
                self.num_freq_entry.focus_set()
                return
            
            times_per_freq = loop_iterations // num_freq
            if sweep_mode == "Log":  
                ratio = (end_freq / start_freq) ** (1 / (num_freq - 1))
                frequencies = [round(start_freq * ratio ** i, 2) for i in range(num_freq) for _ in range(times_per_freq)]
            else:
                step = (end_freq - start_freq) / (num_freq - 1)
                frequencies = [round(start_freq + i * step, 2) for i in range(num_freq) for _ in range(times_per_freq)]

            msg = "Your frequencies are:\n" + ', '.join([format_number(freq) for freq in frequencies]) + "\n\nAre you sure to continue?"
            if not messagebox.askyesno("Confirm Frequencies", msg):
                return
            
        elif sweep_mode == "Custom":
            custom_freqs = self.custom_freq_entry.get().split(',')
            try:
                frequencies = [parse_number(freq.strip()) for freq in custom_freqs]
            except ValueError:
                messagebox.showerror("Error", "Use format like '1M, 2M, 3M' for custom frequencies.")
                self.custom_freq_entry.focus_set()
                return
            if len(frequencies) != loop_iterations:
                messagebox.showerror("Error", "Number of custom frequencies must match loop iterations.")
                self.custom_freq_entry.focus_set()
                return

        selected_actions_index = [index for index, (action, var) in enumerate(self.action_vars.items()) if var.get()]

        print(f"Loop Iterations: {loop_iterations}")
        print(f"Frequencies: {frequencies}")
        print(f"Selected Actions: {selected_actions_index}")
        self.loop_window.grab_release()
        self.loop_window.destroy()
        self.reset_gui_func()
        self.protocol.run_protocol_with_loop(G_var, loop_iterations, frequencies, selected_actions_index)

