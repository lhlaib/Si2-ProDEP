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

        if self.hdwf.value == 0:  # Check if device is opened successfully
            print("Failed to open device")
            raise RuntimeError("Failed to open AD2 device")
        
        # the device will only be configured when FDwf###Configure is called
        self.dwf.FDwfDeviceAutoConfigureSet(self.hdwf, c_int(0))

        # Enable both channels and configure the master-slave relationship
        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), AnalogOutNodeCarrier, c_int(True))
        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), AnalogOutNodeCarrier, c_int(True))
        self.dwf.FDwfAnalogOutMasterSet(self.hdwf, c_int(1), c_int(0))  # Second channel is slave to the first channel
        
        print("Generating sine wave.")
        self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, funcSine)

    def set_wave_parameters(self, freq, phase, voltage):
        """
        Configure the Analog Discovery 2 device with the given frequency, phase, and voltage.

        :param freq: Frequency in Hz
        :param phase: Phase in degrees
        :param voltage: Voltage amplitude in volts
        """
        print(f"Setting waveform parameters: Frequency={freq} Hz, Phase={phase}°, Voltage={voltage} V")

        # Set frequency, amplitude, and offset for both channels
        self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(freq))
        self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(voltage / 2))
        self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(-1), AnalogOutNodeCarrier, c_double(voltage / 2))

        # Set phase for the second channel
        self.dwf.FDwfAnalogOutNodePhaseSet(self.hdwf, c_int(1), AnalogOutNodeCarrier, c_double(phase))

        # Start the waveform generation
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


    