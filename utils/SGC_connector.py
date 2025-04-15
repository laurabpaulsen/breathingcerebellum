import serial
from abc import ABC, abstractmethod
from pathlib import Path
import csv
import numpy as np

class BaseSGCConnector(ABC):
    def __init__(self, intensity_codes_path: Path, start_intensity=1):
        self.command_lookup = self.prep_intensity_codes_lookup(intensity_codes_path)
        self.current_intensity = start_intensity
        self.PULSE_COMMAND = "?*A,S$C0#"
        self.WAKEUP_COMMAND = "?*W$57#"

    def prep_intensity_codes_lookup(self, path):
        lookup = {}
        with open(path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                lookup[float(row[1])] = row[0]
        return lookup

    @abstractmethod
    def send_command(self, command: str):
        pass

    def send_pulse(self):
        self.send_command(self.PULSE_COMMAND)

    def change_intensity(self, target_intensity: float):
        target_intensity = round(target_intensity, 1)

        if self.current_intensity == target_intensity:
            return

        elif self.current_intensity > target_intensity:
            self.send_command(self.command_lookup[target_intensity])
        else:
            if target_intensity - self.current_intensity > 1:
                start = np.ceil(self.current_intensity)
                end = np.floor(target_intensity) + 1
                stepping_stones = np.arange(start, end, 1.0)
                for stone in stepping_stones:
                    self.send_command(self.command_lookup[stone])
            self.send_command(self.command_lookup[target_intensity])

        self.current_intensity = target_intensity

    def set_trigger_delay(self, delay=0):
        if delay not in [0, 50]:
            raise NotImplementedError("Only 0 or 50 ms supported")
        command = "?D,0$A0#" if delay == 0 else "?D,1$A1#"
        self.send_command(command)

    def set_pulse_duration(self, duration=200):
        if duration != 200:
            raise NotImplementedError("Only 200 ms duration supported")
        self.send_command("?L,20$DA#")

    def wakeup(self):
        self.send_command(self.WAKEUP_COMMAND)



class SGCConnector(BaseSGCConnector):
    def __init__(self, port, intensity_codes_path: Path, start_intensity=1, timeout=1):
        super().__init__(intensity_codes_path, start_intensity)
        self.serialport = self.open_serial_port(port, timeout)

    def open_serial_port(self, port, timeout):
        return serial.Serial(port=port, baudrate=38400, timeout=timeout)

    def send_command(self, command: str):
        self.serialport.write(bytes(command, "utf-8"))

    def __del__(self):
        if hasattr(self, "serialport") and self.serialport and self.serialport.is_open:
            self.serialport.close()



class SGCFakeConnector(BaseSGCConnector):
    def __init__(self, intensity_codes_path: Path, start_intensity=1):
        super().__init__(intensity_codes_path, start_intensity)
        self.sent_commands : list[str] = []

    def send_command(self, command: str):
        print(f"[FAKE SEND] {command}")  # or just log it
        self.sent_commands.append(command)
