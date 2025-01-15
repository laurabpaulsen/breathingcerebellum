
from pathlib import Path
import serial
import csv

class SGC_connector:
    def __init__(self, intensity_codes_path:Path, start_intensity = 1):
        
        self.command_lookup = self.prep_intensity_codes_lookup(intensity_codes_path)
        self.current_intensity = start_intensity


    def prep_intensity_codes_lookup(self, path):
        lookup = {}

        with open(path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                lookup[float(row[1])] = row[0]

        print(lookup)

        return lookup

    def open_serial_port(self, port):
        
        self.serialport = serial.Serial(
            port=port,  # Port name (adjust as necessary)
            baudrate=38400,  # Baud rate
        )

    def change_intensity(self, target_intensity:float):

        # check whether to increase or decrease the intensity
        if self.current_intensity > target_intensity: # decreasing intensity can be done easily with out needing to loop
            self.send_command(self.command_lookup[target_intensity])
        else:
            pass # lots of stuff needs to happen here!
        
    def send_command(self, command):
        
        self.serialport.write(command)
        pass

    def set_trigger_delay(self, delay = 0):
        if delay not in [0, 50] :
            NotImplementedError("Currently only setting the trigger delay to 0 is implemented")
        
        if delay == 0:
            self.send_command(b"?D,0$A0#")
        else:
            self.send_command(b"?D,0$A0#")


    def set_pulse_duration(self, duration = 200):
        if duration != 200 :
            NotImplementedError("Currently only setting the duration to 200 is implemented")
        
        self.send_command(b"?L,20$DA#")



if __name__ in "__main__":
    connector = SGC_connector(Path("intensity_code.csv"))
    connector.open_serial_port("/dev/cu.usbserial-110")