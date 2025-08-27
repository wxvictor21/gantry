import gi
import numpy as np
import cv2
import time
import os
from datetime import datetime

gi.require_version("Aravis", "0.8")
from gi.repository import Aravis


class CameraController:
    def __init__(self, ip="192.168.2.202", save_dir="static/photos"):
        print(f"Conectando a la cámara en {ip} ...")
        self.cam = Aravis.Camera.new(ip)
        self.device = self.cam.get_device()

        # 🔹 Restaurar parámetros por defecto
        try:
            self.device.set_string_feature_value("UserSetSelector", "Default")
            self.cam.execute_command("UserSetLoad")
            print("✅ Configuración de fábrica cargada")
        except Exception as e:
            print(f"⚠️ No se pudo aplicar UserSet Default: {e}")

        # Resolución después del reset
        self.width = self.device.get_integer_feature_value("Width")
        self.height = self.device.get_integer_feature_value("Height")
        print(f"Resolución detectada: {self.width}x{self.height}")

        # ───────────────────────────────
        # Detectar PixelFormats soportados
        try:
            formats = self.device.get_available_enumeration_feature_values("PixelFormat")
            supported_formats = [
                self.device.get_enumeration_feature_as_string("PixelFormat", f)
                for f in formats
            ]
            print("Formatos soportados:", supported_formats)
        except Exception as e:
            print(f"No se pudo leer PixelFormats: {e}")
            supported_formats = []

        # Verificar si soporta RGB directo
        self.use_rgb_direct = False
        if "RGB8Packed" in supported_formats:
            print("✅ Usando PixelFormat = RGB8Packed (la cámara envía RGB directo)")
            self.device.set_string_feature_value("PixelFormat", "RGB8Packed")
            self.use_rgb_direct = True
        else:
            print("⚠️ Cámara no soporta RGB8Packed, se usará RAW Bayer + demosaicing")

        # Configuración de trigger software
        self.device.set_string_feature_value("TriggerMode", "On")
        self.device.set_string_feature_value("TriggerSource", "Software")

        # Crear stream y buffers
        self.stream = self.cam.create_stream(None, None)
        payload = self.cam.get_payload()
        for _ in range(10):
            self.stream.push_buffer(Aravis.Buffer.new_allocate(payload))

        self.cam.start_acquisition()

        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def buffer_to_rgb(self, buffer):
        """Convierte un buffer en imagen RGB aplicando demosaicing si es necesario"""
        data = np.frombuffer(buffer, dtype=np.uint8)

        if self.use_rgb_direct:
            # 🔹 La cámara ya entrega RGB
            rgb = data.reshape((self.height, self.width, 3))

        else:
            # 🔹 RAW Bayer → aplicar demosaicing
            raw = data.reshape((self.height, self.width))

            # ⚠️ IMPORTANTE: el patrón depende del sensor → probar RG/GB/BG/GR
            # Aquí uso RGGB por defecto
            bgr = cv2.cvtColor(raw, cv2.COLOR_BayerRG2BGR)

            # Corrección de gamma
            gamma = 1.8
            table = np.array(
                [(i / 255.0) ** (1 / gamma) * 255 for i in np.arange(256)]
            ).astype("uint8")
            bgr = cv2.LUT(bgr, table)

            # Balance de blancos
            try:
                wb = cv2.xphoto.createSimpleWB()
                bgr = wb.balanceWhite(bgr)
            except Exception:
                print("⚠️ cv2.xphoto no disponible → sin balance de blancos")

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        return rgb

    def take_picture(self):
        """Dispara la cámara, guarda imagen y devuelve el array RGB"""
        self.device.execute_command("TriggerSoftware")

        buffer = None
        t0 = time.time()
        while buffer is None and time.time() - t0 < 2:
            buffer_obj = self.stream.try_pop_buffer()
            if buffer_obj:
                buffer = buffer_obj.get_data()
                self.stream.push_buffer(buffer_obj)  # reusar buffer
            time.sleep(0.01)

        if buffer is not None:
            rgb_img = self.buffer_to_rgb(buffer)

            # Guardar imagen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}.png"
            filepath = os.path.join(self.save_dir, filename)
            cv2.imwrite(filepath, cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR))

            print(f"✅ Imagen guardada: {filepath}")
            return filename, rgb_img
        else:
            print("❌ No se recibió ningún frame")
            return None, None

