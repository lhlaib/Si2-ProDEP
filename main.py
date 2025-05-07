# ========================================================
# Project:  BioFPGAG-G6-python
# File:     main.py
# Author:   Lai Lin-Hung @ Si2 Lab
# Date:     2024.10.16
# Version:  v1.0
# ========================================================
# Following files are imported from src folder
# - header.py (define all the global variables)
# - Action.py (define all the actions class)
# - Protocol.py (define the protocol class)
# - Display.py (define the display and AI class)
# - App.py (define the main GUI and dragdrop app)
# - Chip.py (define the controlling chip functions transmit to Resberry Pi by HTTP)
# ========================================================
# Protocol Stores with JSON format in bio-protocol folder
# Pattern Stores with CSV format in pattern folder
# ======================================================== 

from src.header import *

if __name__ == "__main__":
    root = tk.Tk()

    # 啟動主應用程式 (DragDropApp)
    G_var = Global_Var(root)    

    # G_var.dragdrop_app = DragDropApp(root, G_var)
    # 啟動 DEP Action 的圖像和 OBS 顯示
    # dep_action = DEP_Action("Sample DEP Action")
    # dep_action.add_zero_pattern()
    # root2 = tk.Toplevel()  # 創建第二個窗口
    # G_var.display_window = root2
    # dual_display_app = DualDisplayApp(root2, G_var)

    # read default protocol
    G_var.dragdrop_app.load_protocol(G_var,"./bio-protocol/DEP_TEST_70.json")

    root.mainloop()

    