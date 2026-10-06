import serial
import time

# --- CONFIGURACION DE PUERTOS (BASE) ---
# ATENCIÓN: 
# - Si usas Windows, cambia esto a 'COMx' (ej: 'COM4', 'COM5')
# - Si usas Linux, usa '/dev/ttyUSBx' o '/dev/ttyACMx'
PUERTO_GPS_BASE = '/dev/ttyUSB0'   # El puerto donde está conectado el UM980
PUERTO_RADIO_BASE = '/dev/ttyUSB1' # El puerto de la radio transmisora

BAUD_GPS = 115200
BAUD_RADIO = 57600

def main():
    gps_base = None
    radio_base = None
    try:
        print("Iniciando Transmisor de la Base RTK...")
        
        print(f"Abriendo GPS Base en {PUERTO_GPS_BASE}...")
        gps_base = serial.Serial(PUERTO_GPS_BASE, BAUD_GPS, timeout=0.1)

        print(f"Abriendo Radio Base en {PUERTO_RADIO_BASE}...")
        radio_base = serial.Serial(PUERTO_RADIO_BASE, BAUD_RADIO, timeout=0.1)

        while True:
            if gps_base.in_waiting > 0:
                datos_rtcm = gps_base.read(gps_base.in_waiting)
                try:
                    radio_base.write(datos_rtcm)
                except serial.SerialException as e:
                    print(f"Error escribiendo en radio: {e}")

            time.sleep(0.01)

    except serial.SerialException as e:
        print(f"Error de puerto: {e}")
    except KeyboardInterrupt:
        print("\nTransmisión detenida")
    finally:
        if gps_base and gps_base.is_open:
            gps_base.close()
        if radio_base and radio_base.is_open:
            radio_base.close()

if __name__ == '__main__':
    main()