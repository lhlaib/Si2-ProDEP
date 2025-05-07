from tkinter import scrolledtext
from src.Protocol import *

class ScriptRunner:
    def __init__(self, root, G_var: Global_Var):
        self.window = tk.Toplevel(root)
        self.window.title("Run Tcl Script")

        self.text = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, height=20, width=80)
        self.text.pack(expand=True, fill="both")
        self.text.bind("<Control-s>", lambda event: self.run_script())
        self.text.focus_set()

        self.apply_button = ttk.Button(self.window, text="Apply", command=self.run_script, width=10)
        self.apply_button.pack()

        self.tcl = tk.Tcl()
        self.tcl.createcommand("add_DEP_action", self.add_DEP_action)
        # self.tcl.createcommand("delete_action", self.delete_action)
        self.tcl.createcommand("create_protocol", self.create_protocol)
        self.tcl.createcommand("load_protocol", self.load_protocol)
        self.tcl.createcommand("save_protocol", self.save_protocol)
        self.tcl.createcommand("run_action", self.run_action)
        self.tcl.createcommand("run_protocol", self.run_protocol)
        self.tcl.createcommand("update_gui", self.update_gui)

        self.protocol = G_var.protocol
        self.G_var = G_var

    def run_script(self):
        script = self.text.get("1.0", tk.END)
        try:
            self.tcl.eval(script)
        finally:
            self.window.destroy()

    def add_DEP_action(self, action_name, folder_path, pattern_interval, timer_mode ,loop_iterations, loop_interval, frequency, phase, voltage):
        if action_name in [action.action_name for action in self.protocol.actions]:
            raise Exception("Action name \"%s\" already exists."%action_name)
        
        if not os.path.exists(folder_path):
            raise Exception("Folder path \"%s\" does not exist."%folder_path)
        
        action = DEP_Action(action_name)
        pattern_interval = 1000 * float(pattern_interval)
        loop_interval = 1000 * float(loop_interval)
        action.update_action(action_name, folder_path, pattern_interval, timer_mode, loop_interval, loop_iterations, frequency, phase, voltage)
        self.protocol.add_action(action)

    # def delete_action(self):
    #     pass

    def create_protocol(self, protocol_name, protocol_ver):
        self.protocol.reset_protocol(self.G_var)
        self.protocol.name = protocol_name
        self.protocol.version = protocol_ver

    def load_protocol(self, file_path):
        if os.path.exists(file_path):
            self.protocol.load_protocol_from_json(file_path)
        else:
            raise Exception("File path \"%s\" does not exist."%file_path)

    def save_protocol(self, file_name):
        self.protocol.save_protocol_to_json("./bio-protocol/%s.json"%file_name)

    def run_action(self, action_name):
        for action in self.protocol.actions:
            if action.action_name == action_name:
                self.protocol.run_action(action, self.G_var)
                return

    def run_protocol(self):
        self.protocol.run_protocol(self.G_var)

    def update_gui(self):
        self.G_var.dragdrop_app.update_gui_from_protocol(self.G_var)

    def run(self):
        self.window.mainloop()