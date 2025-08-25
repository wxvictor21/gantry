from flask import Flask, request, jsonify, render_template
import serial, time

app = Flask(__name__)
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

def send_grbl(cmd):
    ser.write((cmd + '\n').encode())
    time.sleep(0.1)
    response = []
    while ser.in_waiting:
        response.append(ser.readline().decode().strip())
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    data = request.json
    x_units = data.get('x')
    y_units = data.get('y')

    if x_units is None or y_units is None:
        return jsonify({'error': 'Parámetros X o Y faltantes'}), 400

    try:
        # Conversión de unidades → mm
        x_mm = float(x_units) /  50.0   # 1 unidad en X = 50 mm
        y_mm = float(y_units) / 10.0   # 1 unidad en Y = 10 mm

        # Velocidad fija
        f = 1500  

        cmd = f'G1 X{x_mm:.2f} Y{y_mm:.2f} F{f}'
        resp = send_grbl(cmd)
        return jsonify({'cmd': cmd, 'resp': resp})

    except ValueError:
        return jsonify({'error': 'Valores inválidos'}), 400

@app.route('/status', methods=['GET'])
def status():
    resp = send_grbl('?')
    return jsonify(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
