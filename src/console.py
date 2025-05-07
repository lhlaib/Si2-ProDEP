import tkinter as tk
from tkinter import scrolledtext

'''
start a loop console window to run the protocol 
In this console window, it will read the command from the user

For example, ./run_action [action_name] [iterations] (optional: -sweep [variable] [start] [end] [step] -alter [variable] [value] optional: [variable2] [value2] ...)
For example, ./run_action divide4 2x -sweep frequency 1M 10M 1M
For example, ./run_action divide4 10x -sweep frequency 1M 10M 1M -alter voltage 1.8
For example, ./run_action divide4 10x -alter voltage 1.8
For example, ./run_action divide4 10x -sweep frequency 1M 10M 1M -alter voltage 1.8 -alter phase 180
For example, ./run_action divide4 10x -sweep frequency 1M 10M 1M -alter voltage 1.8 phase 180 -sweep voltage 1.8 2.0 0.1

For example, ./run_protocol [protocol_name] [iterations] (optional: -sweep [variable] [start] [end] [step] -alter [variable] [value] optional: [variable2] [value2] ...)
For example, ./run_protocol DEP_TEST_70 10x -sweep frequency 1M 10M 1M -alter voltage 1.8
For example, ./run_protocol DEP_TEST_70 10x -sweep frequency 1M 10M 1M -alter voltage 1.8 phase 180
For example, ./run_protocol DEP_TEST_70 10x -sweep frequency 1M 10M 1M -alter voltage 1.8 phase 180 -sweep voltage 1.8 2.0 0.1
''' 

class ProtocolConsole:
    def __init__(self, G_var):
        self.root = tk.Tk()
        self.root.title("Protocol Console")
        self.setup_ui()

    def setup_ui(self):
        # Console output area
        self.console_output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20, width=80, font=("Helvetica", 12))
        self.console_output.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        # Command entry field
        self.command_entry = tk.Entry(self.root, width=60, font=("Helvetica", 12))
        self.command_entry.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.command_entry.bind("<Return>", self.handle_command)

        # Submit button
        self.submit_button = tk.Button(self.root, text="Run Command", font=("Helvetica", 12, "bold"), command=self.run_command)
        self.submit_button.grid(row=1, column=1, padx=10, pady=10, sticky="e")

    def append_to_console(self, message):
        """Append a message to the console output."""
        self.console_output.insert(tk.END, f"{message}\n")
        self.console_output.see(tk.END)

    def parse_command(self, command):
        """Custom parser for the protocol and action commands."""
        parts = command.strip().split()
        if not parts:
            raise ValueError("Empty command.")

        if parts[0] == "./run_action":
            return self.parse_action(parts)
        elif parts[0] == "./run_protocol":
            return self.parse_protocol(parts)
        else:
            raise ValueError("Unknown command. Use './run_action' or './run_protocol'.")

    def parse_action(self, parts):
        """Parse the run_action command."""
        if len(parts) < 3:
            raise ValueError("Invalid run_action command. Syntax: ./run_action [action_name] [iterations] [options]")
        
        action_name = parts[1]
        iterations = parts[2]
        options = self.parse_options(parts[3:])
        
        return {
            "type": "action",
            "action_name": action_name,
            "iterations": iterations,
            "options": options
        }

    def parse_protocol(self, parts):
        """Parse the run_protocol command."""
        if len(parts) < 3:
            raise ValueError("Invalid run_protocol command. Syntax: ./run_protocol [protocol_name] [iterations] [options]")
        
        protocol_name = parts[1]
        iterations = parts[2]
        options = self.parse_options(parts[3:])
        
        return {
            "type": "protocol",
            "protocol_name": protocol_name,
            "iterations": iterations,
            "options": options
        }

    def parse_options(self, parts):
        """Parse options like -sweep and -alter."""
        options = []
        i = 0
        while i < len(parts):
            if parts[i] == "-sweep":
                if i + 4 >= len(parts):
                    raise ValueError(f"Invalid -sweep format at index {i}")
                options.append({
                    "type": "sweep",
                    "variable": parts[i + 1],
                    "start": parts[i + 2],
                    "end": parts[i + 3],
                    "step": parts[i + 4]
                })
                i += 5
            elif parts[i] == "-alter":
                alter_variables = []
                i += 1
                while i < len(parts) and not parts[i].startswith("-"):
                    if i + 1 >= len(parts):
                        raise ValueError(f"Invalid -alter format at index {i}")
                    alter_variables.append({
                        "variable": parts[i],
                        "value": parts[i + 1]
                    })
                    i += 2
                options.append({
                    "type": "alter",
                    "variables": alter_variables
                })
            else:
                raise ValueError(f"Unknown option: {parts[i]}")
        return options

    def handle_command(self, event=None):
        """Handle command input and run it."""
        command = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)

        if not command:
            self.append_to_console("Error: No command entered.")
            return

        try:
            parsed_command = self.parse_command(command)
            self.append_to_console(f"> {command}")
            self.run_protocol(parsed_command)
        except Exception as e:
            self.append_to_console(f"Error: {e}")

    def run_command(self):
        """Run the command from the entry box."""
        self.handle_command()

    def run_protocol(self, parsed_command):
        """Simulate running the protocol based on parsed arguments."""
        self.append_to_console(f"Running with parsed command: {parsed_command}")
        self.execute_command(parsed_command)

    def parse_number(self, value):
        """Convert numbers with suffixes (e.g., '1M', '2K') into integers."""
        multiplier = {'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'K': 1e3, 'M': 1e6, 'G': 1e9}
        if value[-1] in multiplier:
            return float(value[:-1]) * multiplier[value[-1]]
        return float(value)

    def execute_command(self, command):
        """Execute the parsed options with nested loops."""
        action_name = command["action_name"]
        iterations = int(command["iterations"].rstrip("xX"))
        options = command["options"]

        # Prepare the loop stack
        loop_ranges = []

        for option in options:
            if option["type"] == "sweep":
                start = self.parse_number(option["start"])
                end = self.parse_number(option["end"])
                step = self.parse_number(option["step"])

                # Handle range depending on step direction
                if step > 0:
                    values = [start + i * step for i in range(int((end - start) / step + 1))]
                else:
                    values = [start + i * step for i in range(int((start - end) / abs(step) + 1))]

                loop_ranges.append({"type": "sweep", "variable": option["variable"], "values": values})

            elif option["type"] == "alter":
                loop_ranges.append({"type": "alter", "variables": option["variables"]})

        # Execute loops
        self.run_nested_loops(loop_ranges, iterations, action_name)

    def run_nested_loops(self, loop_ranges, iterations, action_name):
        """Execute nested loops based on the prepared loop ranges, ensuring correct order."""
        def inner_loop(current_state, depth=0):
            if depth == len(loop_ranges):
                # Innermost loop: Execute iterations
                for _ in range(iterations):
                    self.G_var.protocol.run_action(action_name, self.G_var)
                    self.append_to_console(f"Executing {action_name}()")
                return

            current_loop = loop_ranges[depth]
            if current_loop["type"] == "sweep":
                variable = current_loop["variable"]
                for value in current_loop["values"]:
                    self.append_to_console(f"Sweep Setting {variable} to {value}")
                    current_state[variable] = value  # Update current state
                    inner_loop(current_state, depth + 1)

            elif current_loop["type"] == "alter":
                for variable in current_loop["variables"]:
                    self.append_to_console(f"alter Setting {variable['variable']} to {variable['value']}")
                    current_state[variable['variable']] = variable['value']  # Update current state
                inner_loop(current_state, depth + 1)

        # Start the recursive execution with an empty state
        inner_loop(current_state={})

    def run(self):
        """Start the GUI event loop."""
        self.root.mainloop()


