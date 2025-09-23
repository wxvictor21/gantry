import serial
import time

class GRBLController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def send(self, cmd):
        self.ser.write((cmd + '\n').encode())
        time.sleep(0.1)
        response = []
        while self.ser.in_waiting:
            response.append(self.ser.readline().decode().strip())
        return response

    def move(self, x_units, y_units, f=1500):
        """Convierte unidades en mm y envía comando de movimiento"""
        x_mm = float(x_units) / 50.0   # 1 unidad en X = 50 mm
        y_mm = float(y_units) / 10.0   # 1 unidad en Y = 10 mm
        cmd = f'G1 X{x_mm:.2f} Y{y_mm:.2f} F{f}'
        resp = self.send(cmd)
        return cmd, resp

    def status(self):
        return self.send('?')
