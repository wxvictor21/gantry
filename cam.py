import gi
import numpy as np
import cv2
import time

gi.require_version("Aravis", "0.8")
from gi.repository import Aravis

def main():
    CAMERA_IP = "192.168.2.202"

    print(f"Conectando a la cámara en {CAMERA_IP} ...")
    cam = Aravis.Camera.new(CAMERA_IP)
    device = cam.get_device()

    # Resolución
    width = device.get_integer_feature_value("Width")
    height = device.get_integer_feature_value("Height")
    print(f"Resolución detectada: {width}x{height}")

    # Configuración de trigger software
    device.set_string_feature_value("TriggerMode", "On")
    device.set_string_feature_value("TriggerSource", "Software")

    # Crear stream y empujar varios buffers
    stream = cam.create_stream(None, None)
    payload = cam.get_payload()
    for _ in range(10):
        stream.push_buffer(Aravis.Buffer.new_allocate(payload))

    # Iniciar adquisición
    cam.start_acquisition()

    # Mandar trigger software
    print("Enviando trigger ...")
    device.execute_command("TriggerSoftware")

    # Intentar leer buffer con timeout manual
    buffer = None
    t0 = time.time()
    while buffer is None and time.time() - t0 < 2:  # 2 segundos máx
        buffer = stream.try_pop_buffer()
        time.sleep(0.01)

    if buffer:
        data = buffer.get_data()
        arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width))

        # BayerBG8 -> RGB
        rgb = cv2.cvtColor(arr, cv2.COLOR_BayerBG2BGR)

        cv2.imwrite("captura.png", rgb)
        print("Imagen guardada como captura.png")

        stream.push_buffer(buffer)
    else:
        print("o se recibió ningún frame")

    cam.stop_acquisition()

if __name__ == "__main__":
    main()
