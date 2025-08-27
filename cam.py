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

    # ───────────────────────────────
    # Detectar PixelFormats soportados
    try:
        formats = device.get_available_enumeration_feature_values("PixelFormat")
        supported_formats = [device.get_enumeration_feature_as_string("PixelFormat", f) for f in formats]
        print("Formatos soportados:", supported_formats)
    except Exception as e:
        print(f"No se pudo leer PixelFormats: {e}")
        supported_formats = []

    # Intentar configurar RGB8Packed si está disponible
    use_rgb_direct = False
    if "RGB8Packed" in supported_formats:
        print("✅ Usando PixelFormat = RGB8Packed (la cámara envía RGB)")
        device.set_string_feature_value("PixelFormat", "RGB8Packed")
        use_rgb_direct = True
    else:
        print("⚠️ La cámara no soporta RGB8Packed, se usará Bayer + corrección")

    # Configuración de trigger software
    device.set_string_feature_value("TriggerMode", "On")
    device.set_string_feature_value("TriggerSource", "Software")

    # Crear stream y empujar buffers
    stream = cam.create_stream(None, None)
    payload = cam.get_payload()
    for _ in range(10):
        stream.push_buffer(Aravis.Buffer.new_allocate(payload))

    # Iniciar adquisición
    cam.start_acquisition()

    # Mandar trigger
    print("Enviando trigger ...")
    device.execute_command("TriggerSoftware")

    buffer = None
    t0 = time.time()
    while buffer is None and time.time() - t0 < 2:
        buffer = stream.try_pop_buffer()
        time.sleep(0.01)

    if buffer:
        data = buffer.get_data()

        if use_rgb_direct:
            # La cámara ya entrega RGB
            arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
            img_rgb = arr

        else:
            # RAW Bayer -> RGB con corrección
            arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width))

            # Demosaicing
            bgr = cv2.cvtColor(arr, cv2.COLOR_BayerRG2BGR)

            # Corrección de gamma (aclarar)
            gamma = 1.8
            table = np.array([(i / 255.0) ** (1/gamma) * 255 for i in np.arange(256)]).astype("uint8")
            bgr = cv2.LUT(bgr, table)

            # Balance de blancos automático de OpenCV
            result = cv2.xphoto.createSimpleWB()
            bgr = result.balanceWhite(bgr)

            img_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # Guardar
        cv2.imwrite("captura.png", cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
        print("✅ Imagen guardada como captura.png")

        stream.push_buffer(buffer)
    else:
        print("❌ No se recibió ningún frame")

    cam.stop_acquisition()

if __name__ == "__main__":
    main()
