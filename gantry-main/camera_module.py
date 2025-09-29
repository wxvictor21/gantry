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
        print(f"Conectando a la cámara Cognex en {ip} ...")
        self.cam = Aravis.Camera.new(ip)
        self.device = self.cam.get_device()

        # 🔹 Restaurar parámetros por defecto
        try:
            self.device.set_string_feature_value("UserSetSelector", "Default")
            self.cam.execute_command("UserSetLoad")
            print("Configuración de fábrica cargada")
        except Exception as e:
            print(f"Advertencia: No se pudo aplicar UserSet Default (posiblemente acceso denegado o cámara en uso): {e}")

        # Resolución después del reset
        self.width = self.device.get_integer_feature_value("Width")
        self.height = self.device.get_integer_feature_value("Height")
        print(f"Resolución detectada: {self.width}x{self.height}")

        # ───────────────────────────────
        # Detectar PixelFormats soportados
        supported_formats = []
        try:
            formats = self.device.get_available_enumeration_feature_values("PixelFormat")
            supported_formats = [
                self.device.get_enumeration_feature_as_string("PixelFormat", f)
                for f in formats
            ]
            print("Formatos soportados:", supported_formats)
        except AttributeError:
            print("Advertencia: 'get_available_enumeration_feature_values' no disponible. Asumiendo que RGB8Packed no es directamente soportado.")
        except Exception as e:
            print(f"No se pudo leer PixelFormats: {e}")

        # Verificar si soporta RGB directo
        self.use_rgb_direct = False
        if "RGB8Packed" in supported_formats:
            try:
                self.device.set_string_feature_value("PixelFormat", "RGB8Packed")
                self.use_rgb_direct = True
                print("Usando PixelFormat = RGB8Packed (la cámara envía RGB directo)")
            except Exception as e:
                print(f"No se pudo aplicar RGB8Packed: {e}")
                print("Cámara no soporta RGB8Packed → se usará RAW Bayer + demosaicing")
        else:
            print("Cámara no soporta RGB8Packed → se usará RAW Bayer + demosaicing")

        # ───────────────────────────────
        # Intentar configurar trigger software (si la cámara lo permite)
        self.software_trigger = False
        try:
            self.device.set_string_feature_value("TriggerMode", "On")
            self.device.set_string_feature_value("TriggerSource", "Software")
            self.software_trigger = True
            print("TriggerMode=On (Software) configurado")
        except Exception as e:
            print(f"Advertencia: No se pudo activar TriggerMode/Source (posiblemente acceso denegado o no soportado): {e}")
            print("⚠️ La cámara continuará en modo por defecto (free-run)")

        # ───────────────────────────────
        # Crear stream y buffers
        try:
            self.stream = self.cam.create_stream(None, None)
        except Exception as e:
            print(f"❌ No se pudo crear stream (posiblemente se requiere privilegio de controlador o cámara en uso): {e}")
            self.stream = None  # Continuar sin stream para evitar crashear

        if self.stream:
            payload = self.cam.get_payload()
            for _ in range(10):
                self.stream.push_buffer(Aravis.Buffer.new_allocate(payload))
            self.cam.start_acquisition()

        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    # ---------------------------------------------------------------------
    def buffer_to_rgb(self, buffer):
        """Convierte un buffer en imagen RGB aplicando demosaicing si es necesario"""
        data = np.frombuffer(buffer, dtype=np.uint8)

        if self.use_rgb_direct:
            rgb = data.reshape((self.height, self.width, 3))
        else:
            raw = data.reshape((self.height, self.width))
            bgr = cv2.cvtColor(raw, cv2.COLOR_BayerBG2BGR)

            # Corrección de gamma
            gamma = 1.0
            table = np.array(
                [(i / 255.0) ** (1 / gamma) * 255 for i in np.arange(256)]
            ).astype("uint8")
            bgr = cv2.LUT(bgr, table)

            # Balance de blancos (si OpenCV xphoto está disponible)
            try:
                wb = cv2.xphoto.createSimpleWB()
                bgr = wb.balanceWhite(bgr)
            except Exception:
                print("cv2.xphoto no disponible → sin balance de blancos")

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        return rgb

    # ---------------------------------------------------------------------
    def take_picture(self):
        """Dispara la cámara (si es posible), guarda imagen y devuelve el array RGB"""
        if self.stream is None:
            print("❌ Stream no disponible → no se puede capturar imagen")
            return None, None

        if self.software_trigger:
            try:
                self.device.execute_command("TriggerSoftware")
            except Exception as e:
                print(f"⚠️ Error al disparar TriggerSoftware: {e}")

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

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}.png"
            filepath = os.path.join(self.save_dir, filename)
            cv2.imwrite(filepath, rgb_img)

            print(f"Imagen guardada: {filepath}")
            return filename, rgb_img
        else:
            print("❌ No se recibió ningún frame")
            return None, None

    # ---------------------------------------------------------------------
    def get_frame_as_jpeg_bytes(self):
        """Captura un frame usando take_picture, lo convierte a JPEG y devuelve los bytes."""
        filename, rgb_img = self.take_picture()
        if rgb_img is not None:
            # Convertir a JPEG
            ret, jpeg = cv2.imencode('.jpg', cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR))
            return jpeg.tobytes() if ret else None
        else:
            return None
