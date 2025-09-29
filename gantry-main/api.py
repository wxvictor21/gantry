"""
Flask API para Gantry (GRBL + Cámara)
- Manejo CORS manual en after_request (no requiere flask-cors).
- Si PREFER_RESTRICTED_CORS=True (env), solo permite ORIGIN_ALLOWED.
- Si ENV=production (env var), sirve una carpeta static/www (build de React).
"""

import os
import time
from flask import Flask, Response, request, jsonify, send_from_directory, abort, make_response
import camera_module
import grbl_module

# Initialize GRBL (Note: This will create new instances alongside existing ones)
# The camera instantiation below is the correct one.
# cam = camera_module.Camera() # Removed as it's causing an error and is redundant.


def gen_frames():
    while True:
        frame = camera.get_frame_as_jpeg_bytes()
        if frame is not None:
            yield (b'--frame\n'
                   b'Content-Type: image/jpeg\n\n' + frame + b'\n')
        else:
            # If no frame is available, wait a bit before trying again
            time.sleep(0.1)


# Importa tus controladores existentes
# Asegúrate de que camera_module.py y grbl_module.py estén en el mismo paquete/path
from camera_module import CameraController
from grbl_module import GRBLController

GRBL_PORT = "/dev/ttyUSB0"
GRBL_BAUD = 115200

# Directorio para imágenes y para servir React build en producción
BASE_DIR = os.path.dirname(__file__)
PHOTOS_DIR = os.path.join(BASE_DIR, "static", "photos")
# REACT_BUILD_DIR = os.path.join(BASE_DIR, "static", "www")  # sitúa aquí tu build de React si quieres servirla

# Crear carpetas si faltan
os.makedirs(PHOTOS_DIR, exist_ok=True)
# if ENV == "production":
#     os.makedirs(REACT_BUILD_DIR, exist_ok=True)

# Instanciar controladores (puede lanzar excepciones si no hay hardware; en dev puedes mockear)
camera = CameraController(CAMERA_IP)
grbl = GRBLController(GRBL_PORT, GRBL_BAUD)

# App Flask
app = Flask(__name__)

# ----------------------------
# Endpoints API
# ----------------------------
@app.get("/api/status")
def status():
    """Devuelve estado de GRBL (respuesta de '?')"""
    try:
        resp = grbl.status()
    except Exception as e:
        return jsonify({"error": "GRBL error", "message": str(e)}), 500
    return jsonify({"grbl": resp})

@app.post("/api/move")
def move():
    """Mover X,Y (POST JSON {x, y, f?})"""
    data = request.get_json() or {}
    x = data.get("x")
    y = data.get("y")
    f = data.get("f", 1500)
    if x is None or y is None:
        return jsonify({"error": "x and y required"}), 400
    try:
        cmd, resp = grbl.move(x, y, f=f)
    except Exception as e:
        return jsonify({"error": "GRBL move failed", "message": str(e)}), 500
    return jsonify({"cmd": cmd, "response": resp})

@app.post("/api/capture")
def capture():
    """Dispara la cámara y devuelve la URL pública de la imagen guardada"""
    try:
        filename, img = camera.take_picture()
    except Exception as e:
        return jsonify({"error": "camera error", "message": str(e)}), 500

    if filename:
        return jsonify({"status": "captured", "file": f"/api/photos/{filename}"})
    else:
        return jsonify({"status": "error", "message": "No frame received"}), 500

@app.get("/api/gallery")
def gallery():
    """Lista las fotos guardadas (URLs relativas)"""
    try:
        files = sorted([f for f in os.listdir(PHOTOS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    except Exception as e:
        return jsonify({"error": "listing photos", "message": str(e)}), 500
    urls = [f"/api/photos/{fname}" for fname in files]
    return jsonify({"photos": urls})

@app.get("/api/photos/<path:filename>")
def photos(filename):
    """Sirve las imágenes guardadas"""
    try:
        return send_from_directory(PHOTOS_DIR, filename, as_attachment=False)
    except Exception as e:
        return jsonify({"error": "file not found", "message": str(e)}), 404

@app.post("/api/sequence")
def sequence():
    """Ejecuta una secuencia simple: movimientos + capturas"""
    data = request.get_json() or {}
    num_shots = int(data.get("num_shots", 1))
    step_x = float(data.get("step_x", 1.0))
    step_y = float(data.get("step_y", 1.0))
    start_x = float(data.get("start_x", 0))
    start_y = float(data.get("start_y", 0))

    photos = []
    shot_count = 0
    try:
        for i in range(num_shots):
            # ejemplo raster (puedes adaptar a tu lógica)
            x = start_x + (i % max(1, int(num_shots))) * step_x
            y = start_y + (i // max(1, int(num_shots))) * step_y
            grbl.move(x, y)
            filename, img = camera.take_picture()
            if filename:
                photos.append(f"/api/photos/{filename}")
            shot_count += 1
            time.sleep(0.1)
    except Exception as e:
        return jsonify({"error": "sequence failed", "message": str(e)}), 500

    return jsonify({"num_shots": shot_count, "photos": photos})

# ----------------------------
# (Opcional) Servir React build en producción
# ----------------------------
if __name__ == "__main__":
    # Nota: en producción usa gunicorn/uWSGI y nginx; el dev server de Flask NO es recomendado para producción.
    app.run(host="0.0.0.0", port=5000)
