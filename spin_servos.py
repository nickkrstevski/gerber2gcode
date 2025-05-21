import serial
import serial.tools.list_ports
import time
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)

class Tool():
    def __init__(self, sn):
        self.sn = sn
        self.ser = self._initialize_serial_connection(self.sn)
        time.sleep(2) # Initialize arduino after serial connection made

    def _initialize_serial_connection(self, sn, baudrate=9600, timeout=1)->serial.Serial:
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in ports:
            print(f"{port}: {desc} [{hwid}]")
        """Initialize and return a serial connection."""
        for port, desc, hwid in ports:
            if sn in hwid:
                try:
                    ser = serial.Serial(port, baudrate, timeout=timeout)
                    print(f"Connected to {port} at {baudrate} baud.")
                    return ser
                except serial.SerialException as e:
                    print(f"Failed to connect to {sn}: {e}")
        return None
    
    def tool_on(self):
        self.send_command("ON\n")

    def tool_off(self):
        self.send_command("OFF\n")

    def send_command(self, command: str):
        """Send a command to the serial device and read the response."""
        if self.ser and self.ser.is_open:
            print("SEND TOOL CMD")
            self.ser.write(command.encode('utf-8'))
            self.ser.flush()
        else:
            print(f"Serial connection to {self.ser.port} is not open.")
            # raise Exception
        

class Axis():
    def __init__(self, sn: str):
        self.sn = sn
        self.origin = 0
        self.position = 0
        self.angle = 0
        self.radius = 6.4
        self.velocity = 0
        self.angle_target = 0
        self.ser = self._initialize_serial_connection(sn)
        self._listen_for_message(">")
        self.init_motion()
        self.velocity_limit = 20
    
    def _initialize_serial_connection(self, sn, baudrate=115200, timeout=0.1)->serial.Serial:
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in ports:
            print(f"{port}: {desc} [{hwid}]")
        """Initialize and return a serial connection."""
        for port, desc, hwid in ports:
            if sn in hwid:
                try:
                    ser = serial.Serial()
                    ser = serial.Serial(port, baudrate, timeout=timeout)
                    print(f"Connected to {port} at {baudrate} baud.")
                    return ser
                except serial.SerialException as e:
                    print(f"Failed to connect to {sn}: {e}")
        return None

    def _listen_for_message(self, target_message):
        """Listen to a serial device until the target message is received."""
        print(f"Listening on {self.ser.port} for '{target_message}'...")
        while True:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()
                print(f"Received from {self.ser.port}: {line}")
                if target_message in line:
                    print(f"'{target_message}' received on {self.ser.port}")
                    return

    def send_command(self, command: str):
        """Send a command to the serial device and read the response."""
        try:
            if self.ser and self.ser.is_open:
                self.ser.write(command.encode('utf-8'))
                self.ser.flush()
            else:
                print(f"Serial connection to {self.ser.port} is not open.")
                # raise Exception
        except:
            self._reconnect_serial()

    def init_motion(self):
        init_commands = ['MLV20\n','MC2\n', 'MAP50\n','MAD1.1\n','M0\n']
        for cmd in init_commands:
            self.send_command(cmd)

    def set_pid(self, p:float, i:float, d:float):
        self.send_command(f"MAP{p}\n")
        self.send_command(f"MAI{i}\n")
        self.send_command(f"MAD{d}\n")
    
    def update_telemetry(self):
        up = False
        uv = False
        ut = False
        # logging.debug(f"TELEMETRY{self.ser.in_waiting}")
        try:
            while not (up and uv and ut):
                while self.ser.in_waiting > 10:
                    self.ser.readline()
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if not line.startswith('>'):
                        return
                    try:
                        content = line[1:].strip()
                        var_name, value_str = content.split(':', 1)
                        value = round(float(value_str),3)
                        if var_name == "9":
                            self.angle = value
                            self.position = round(self.angle*self.radius,3)
                            up = True
                            # logging.debug(f"angle: {self.angle}")
                        elif var_name == "17":
                            self.velocity = value
                            uv = True
                            logging.debug(f"velocity: {self.velocity}")
                        elif var_name == "1":
                            self.angle_target = value
                            ut = True
                            # logging.debug(f"angle_target: {self.angle_target}")

                    except ValueError:
                        continue
                    # print(f"Received from {self.ser.port}: {line}")
        except:
            self._reconnect_serial()

    def _reconnect_serial(self):
        print("RESET SERIAL")
        self.ser.close()
        self.ser.open()


    def set_target_angle_rad(self, target_angle_rad):
        target = round(self.origin+target_angle_rad,2)
        # logging.debug(f"set target M{target}\n")
        self.send_command(f"M{target}\n")

    def set_target_pos_mm(self, target_pos_mm):
        target_angle_rad = round(target_pos_mm/self.radius,2)
        self.set_target_angle_rad(target_angle_rad=target_angle_rad)

    def set_velocity_limit(self, limit):
        self.velocity_limit = limit
        self.send_command(f"MLV{limit}\n")

    def find_home(self):
        self.origin=0
        self.update_telemetry()
        self.set_velocity_limit(20)
        self.send_command("M-100\n")
        # self.ser.reset_input_buffer()
        # self.ser.reset_output_buffer()
        time.sleep(1)
        while self.origin == 0:
            self.update_telemetry()
            if abs(self.velocity)<0.02:
                self.origin = self.angle
                self.set_target_angle_rad(0.5)
                logging.debug(f"origin set to {self.origin}")
                time.sleep(1)

    def mm2rad(self, mm):
        angle_rad = round(mm/self.radius,2)
        return angle_rad
        
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Closed connection to {self.sn}.")

class Gantry():
    def __init__(self, x_axis: Axis, y_axis: Axis, tool = Tool):
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.tool = tool
        self.x = None
        self.y = None

    def set_xy(self, x_pos_mm, y_pos_mm):
        '''
        Set x and y position, give the motor enough time to get there based on telemetry update
        '''
        delay = 1
        fudge = 1
        if self.x and self.y:
            radians_to_go = self.x_axis.mm2rad(x_pos_mm - self.x)
            est_time_1 = fudge*radians_to_go/(self.x_axis.velocity_limit-10)
            print(f"x-distance: {x_pos_mm - self.x}")
            print(f"x-rads: {self.x_axis.mm2rad(x_pos_mm - self.x)}")
            print(f"x-est: {est_time_1}")
            radians_to_go = self.y_axis.mm2rad(y_pos_mm - self.y)
            est_time_2 = fudge*radians_to_go/(self.y_axis.velocity_limit-10)
            print(f"y-distance: {y_pos_mm - self.y}")
            print(f"y-rads: {self.y_axis.mm2rad(y_pos_mm - self.y)}")
            print(f"y-est: {est_time_2}")
            delay = max(abs(est_time_1),abs(est_time_2))
            print(f"DELAY{delay}")

        self.x = x_pos_mm
        self.y = y_pos_mm
        self.x_axis.set_target_pos_mm(x_pos_mm)
        self.y_axis.set_target_pos_mm(y_pos_mm)
        time.sleep(delay)
        # time.sleep(0.005)
        # time.sleep(max(abs(est_time_1),abs(est_time_2)))

    def purge(self,time_s = 1):
        self.set_xy(0,500)
        self.tool.tool_on()
        time.sleep(time_s)
        self.tool.tool_off()

    def run_gcode(self, file_path):
        self.purge(2)
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.split()
                if len(parts) == 0: continue
                cmd = parts[0]
                if cmd == "G1":
                    x = float(parts[1].strip("X"))
                    y = float(parts[2].strip("Y"))
                    # print(f"{x}-{y}")
                    self.set_xy(x,y)
                elif cmd == "M3":
                    self.tool.tool_on()
                elif cmd == "M5":
                    self.tool.tool_off()



def main():
    # Replace 'COM1' and 'COM2' with your actual port names
    global tool_head
    tool_head = Tool(sn="3423931353535120B1E0")
    long_motor_sn = '209D3077484E'
    long_motor = Axis(sn=long_motor_sn)
    short_motor_sn = '205D305F484E'
    short_motor = Axis(sn=short_motor_sn)
    gantry = Gantry(long_motor,short_motor,tool=tool_head)

    short_motor.find_home()
    long_motor.find_home()
    time.sleep(1)
    short_motor.set_velocity_limit(50)
    long_motor.set_velocity_limit(50)
    long_motor.set_pid(p=50,i=0,d=1.3)
    short_motor.set_pid(p=50,i=0,d=1.1)
    # time.sleep(1)
    # long_motor.set_target_pos_mm(100)
    # short_motor.set_target_pos_mm(100)

    #######################################
    try:
        while 1:
            if input('spray?').lower() == "y":
                gantry.run_gcode("./output.gcode")
                # gantry.run_gcode("./circle.gcode")
                # gantry.run_gcode("./infill.gcode")
            if input('again?').lower() == "n":
                kill(gantry)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting gracefully.")
        kill(gantry)

def kill(gantry: Gantry):
    gantry.tool.tool_off()
    print("TURNED STUFF OFF")
    exit()
        

if __name__ == "__main__":
    main()