from ctypes import *
import time
from src.dwfconstants import *
import sys

class AD2Controller:
    def __init__(self):
        if sys.platform.startswith("win"):
            self.dwf = cdll.dwf
        elif sys.platform.startswith("darwin"):
            self.dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
        else:
            self.dwf = cdll.LoadLibrary("libdwf.so")

        self.hdwf = c_int()
        self.version = create_string_buffer(16)

        # Initialize the device
        self.dwf.FDwfGetVersion(self.version)
        print("DWF Version: " + self.version.value.decode())

        self.dwf.FDwfParamSet(DwfParamOnClose, c_int(0))  # 0 = run, 1 = stop, 2 = shutdown

    def open_device(self):
        print("Opening first device...")
        self.dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))

        if self.hdwf.value == 0:
            print("Failed to open device")
            raise RuntimeError("Failed to open AD2 device")
        
        self.dwf.FDwfDeviceAutoConfigureSet(self.hdwf, c_int(0))

        # 正弦波設置 (保持不變)
        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), AnalogOutNodeCarrier, c_int(True))
        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), AnalogOutNodeCarrier, c_int(True))
        self.dwf.FDwfAnalogOutMasterSet(self.hdwf, c_int(1), c_int(0))
        print("Generating sine wave.")
        self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, funcSine)

        # 設置 1.8V 電源供應
        print("Setting up 1.8V supply on V+...")
        self.dwf.FDwfAnalogIOEnableSet(self.hdwf, c_int(1))
        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(0), c_double(1.0))
        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(1), c_double(1.8))
        self.dwf.FDwfAnalogIOConfigure(self.hdwf)  # 添加這一行

        # 設置 DIO7 為 3.3V 靜態輸出
        print("Setting DIO2 to DIO7 to 3.3V static output...")
        mask = sum(1 << i for i in range(2, 8))  # 計算 DIO2~DIO7 的位元遮罩
        output_enable = c_uint(mask)
        self.dwf.FDwfDigitalIOOutputEnableSet(self.hdwf, output_enable)
        output_state = c_uint(mask)
        self.dwf.FDwfDigitalIOOutputSet(self.hdwf, output_state)
        self.dwf.FDwfDigitalIOConfigure(self.hdwf)  # 配置生效
        # 檢查輸出 (可選)
        voltage = c_double()
        self.dwf.FDwfAnalogIOChannelNodeStatus(self.hdwf, c_int(0), c_int(1), byref(voltage))
        print(f"V+ Voltage: {voltage.value}V")
        state = c_uint()
        self.dwf.FDwfDigitalIOStatus(self.hdwf)
        self.dwf.FDwfDigitalIOInputStatus(self.hdwf, byref(state))
        print(f"DIO7 State: {1 if (state.value & (1 << 7)) else 0}")

    # def set_wave_parameters(self, freq, phase, voltage):
    #     """
    #     Configure the Analog Discovery 2 device with the given frequency, phase, and voltage.

    #     :param freq: Frequency in Hz
    #     :param phase: Phase in degrees
    #     :param voltage: Voltage amplitude in volts
    #     """
    #     print(f"Setting waveform parameters: Frequency={freq} Hz, Phase={phase}°, Voltage={voltage} V")

    #     # Set frequency, amplitude, and offset for both channels
    #     self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(freq))
    #     self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(voltage / 2))
    #     self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(voltage / 2))

    #     # Set phase for the second channel
    #     self.dwf.FDwfAnalogOutNodePhaseSet(self.hdwf, c_int(1), AnalogOutNodeCarrier, c_double(phase))

    #     # Start the waveform generation
    #     self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(-1), c_int(1))
    #     print("Waveform generation started.")



    def set_wave_parameters(self, freq, phase, voltage):
        """
        Configure the Analog Discovery 2 device with the given frequency, phase, and voltage.
        Only update frequency if it has changed.

        :param freq: Frequency in Hz
        :param phase: Phase in degrees
        :param voltage: Voltage amplitude in volts
        """
        print(f"Requested waveform parameters: Frequency={freq} Hz, Phase={phase}°, Voltage={voltage} V")

        # 檢查當前頻率
        current_freq = c_double()
        channel = c_int(0)  # 明確指定通道 0
        result = self.dwf.FDwfAnalogOutNodeFrequencyGet(self.hdwf, channel, AnalogOutNodeCarrier, byref(current_freq))
        if result == 0:
            # 獲取錯誤訊息
            error_msg = create_string_buffer(512)
            self.dwf.FDwfGetLastErrorMsg(error_msg)
            print(f"Error: Failed to read frequency. Error message: {error_msg.value.decode()}")
            return
        current_freq = current_freq.value
        print(f"Current frequency: {current_freq} Hz")

        # 如果頻率不變，跳過頻率設定
        if abs(current_freq - freq) < 1:
            print("Frequency unchanged, skipping frequency update.")
        else:
            print(f"Updating frequency from {current_freq} Hz to {freq} Hz")
            self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, channel, AnalogOutNodeCarrier, c_double(freq))
        # 設定振幅和偏移
        self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(voltage / 2))
        self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(voltage / 2))

        # 設定第二通道的相位
        self.dwf.FDwfAnalogOutNodePhaseSet(self.hdwf, c_int(1), AnalogOutNodeCarrier, c_double(phase))

        # 啟動波形生成
        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(-1), c_int(1))
        print("Waveform generation started.")



    def stop_waveform(self):
        """
        Stop the waveform generation.
        """
        print("Stopping waveform generation.")
        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(-1), c_int(0))

    def close_device(self):
        """
        Close the device.
        """
        print("Closing the device.")
        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(-1), c_int(0))
        self.dwf.FDwfAnalogOutReset(self.hdwf, c_int(-1))
        self.dwf.FDwfDeviceClose(self.hdwf)

    def __del__(self):
        self.close_device()


    