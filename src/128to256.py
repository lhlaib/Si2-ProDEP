import os
import re
import numpy as np
import csv
from tkinter import Tk, filedialog, messagebox, Button, Label

def read_and_repeat_csv(input_csv_path, output_csv_path):
    """
    Read a 128x128 CSV file and repeat the array 4 times to create a 256x256 array.

    Args:
        input_csv_path (str): Path to the input 128x128 CSV file.
        output_csv_path (str): Path to save the output 256x256 CSV file.

    Returns:
        None
    """
    with open(input_csv_path, 'r') as file:
        reader = csv.reader(file)
        array_128x128 = np.array([list(map(int, row)) for row in reader])

    if array_128x128.shape != (128, 128):
        raise ValueError(f"Input CSV file {input_csv_path} does not contain a 128x128 array.")

    array_256x256 = np.tile(array_128x128, (2, 2))

    with open(output_csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(array_256x256)

def read_and_process_folder(folder_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    file_tuples = []
    
    for file in files:
        match = re.search(r'(\d+)', file)
        if match:
            number = int(match.group(1))
            file_tuples.append((number, file))

    file_tuples.sort(key=lambda x: x[0])
    sorted_files = [t[1] for t in file_tuples]

    if not sorted_files:
        print("No valid CSV files found.")
        return

    for file in sorted_files:
        input_path = os.path.join(folder_path, file)
        output_path = os.path.join(output_folder, file)

        try:
            read_and_repeat_csv(input_path, output_path)
            print(f"Processed {file} into {output_path}")
        except Exception as e:
            print(f"Error processing {file}: {e}")

    print("All patterns processed and saved.")

def select_folder():
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(initialdir="./pattern", title="Select Folder")

    if folder_selected:
        #remove the last folder "/" and add "_256" to the folder name
        output_folder = folder_selected[:] + "_256"
        # output_folder = os.path.join(folder_selected, "_256")
        try:
            read_and_process_folder(folder_selected, output_folder)
            messagebox.showinfo("Success", f"All patterns have been processed and saved in {output_folder}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    else:
        messagebox.showwarning("Warning", "No folder selected.")

def main_gui():
    root = Tk()
    root.title("Pattern Processor")

    label = Label(root, text="Select a folder to process 128x128 CSV files:")
    label.pack(pady=10)

    button = Button(root, text="Select Folder", command=select_folder)
    button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main_gui()
