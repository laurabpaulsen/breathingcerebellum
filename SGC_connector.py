
from pathlib import Path
import serial
import csv
import numpy as np

class SGC_connector:
    def __init__(self, port, intensity_codes_path:Path, start_intensity = 1, timeout = 1):
        
        self.command_lookup = self.prep_intensity_codes_lookup(intensity_codes_path)
        self.current_intensity = start_intensity
        self.serialport = self.open_serial_port(port=port, timeout=timeout)

        self.PULSE_COMMAND = "?*A,S$C0#"
        self.WAKEUP_COMMAND = "?*W$57#"


    def prep_intensity_codes_lookup(self, path):
        lookup = {}

        with open(path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                lookup[float(row[1])] = row[0]

        return lookup

    def open_serial_port(self, port, timeout=1):
        
        serialport = serial.Serial(
            port=port,  # Port name (adjust as necessary)
            baudrate=38400,  # Baud rate
            timeout=timeout
        )

        return serialport

        
    def send_command(self, command:str):
        self.serialport.write(bytes(command, "utf-8"))


    def send_pulse(self):
        self.send_command(self.PULSE_COMMAND)
    
    def change_intensity(self, target_intensity:float):
        """
        Adjust the stimulus intensity of the SCG to the specified target value.

        Parameters:
            target_intensity (float): The desired intensity level (1 decimal place).
        """

        # round to one decimal place to match command_lookup
        target_intensity = round(target_intensity, 1)

        # check whether to increase, decrease or do nothing with the intensity
        if self.current_intensity == target_intensity:
            pass # no action needed
        
        elif self.current_intensity > target_intensity: # decreasing intensity 
            self.send_command(self.command_lookup[target_intensity])
        
        else: # increasing intensity
            if target_intensity - self.current_intensity > 1: # we need to raise intensity with maximum 1mA at a time
                # generate intermediate intensity steps
                start = np.ceil(self.current_intensity) 
                end = np.floor(target_intensity) + 1

                stepping_stones = np.arange(start, end, 1.0)
                
                for stone in stepping_stones:
                    self.send_command(self.command_lookup[stone])

            # ensure final command is send
            self.send_command(self.command_lookup[target_intensity])


    def set_trigger_delay(self, delay = 0):
        if delay not in [0, 50] :
            NotImplementedError("Currently only setting the trigger delay to 0 or 50 is implemented")
        
        if delay == 0:
            self.send_command("?D,0$A0#")
        elif delay == 50:
            self.send_command("?D,1$A1#")


    def set_pulse_duration(self, duration = 200):
        if duration != 200 :
            NotImplementedError("Currently only setting the duration to 200 is implemented")
        
        self.send_command("?L,20$DA#")

    def wakeup(self):
        self.send_command(self.WAKEUP_COMMAND)

    def __del__(self):
        if self.serialport and self.serialport.is_open:
            self.serialport.close()