from flask import Flask, request, jsonify, render_template, send_from_directory
from camera_module import CameraController
from grbl_module import GRBLController
import os

# Instancias de hardware
camera = CameraController("192.168.2.202")
grbl = GRBLController("/dev/ttyUSB0", 115200)

app = Flask(__name__)

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
        cmd, resp = grbl.move(x_units, y_units)
        photo = camera.take_picture()
        if photo:
            return jsonify({
                'cmd': cmd,
                'resp': resp,
                'photo_url': f'/photos/{photo}'
            })
        else:
            return jsonify({'cmd': cmd, 'resp': resp, 'error': 'No se pudo capturar imagen'})
    except ValueError:
        return jsonify({'error': 'Valores inválidos'}), 400

@app.route('/status')
def status():
    return jsonify(grbl.status())

@app.route('/gallery')
def gallery():
    files = sorted(os.listdir("static/photos"), reverse=True)
    return render_template('gallery.html', photos=files)

@app.route('/photos/<filename>')
def photos(filename):
    return send_from_directory("static/photos", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
