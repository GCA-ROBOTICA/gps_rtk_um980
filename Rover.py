import serial
import time

# IMPORTANTE: Verifica que estos sean tus puertos reales al hacer usbipd
PUERTO_RADIO = '/dev/ttyUSB0' 
PUERTO_GPS = '/dev/ttyUSB1'

def main():
    print("Iniciando Inyector Ciego RTCM3...")
    try:
        radio = serial.Serial(PUERTO_RADIO, 57600, timeout=0.1)
        gps = serial.Serial(PUERTO_GPS, 115200, timeout=0.1)
        
        # 1. Le damos el "grito" inicial al GPS para asegurarnos de que hable
        comando_inicio = "unlog\r\nmode rover\r\ngngga com1 0.1\r\n"
        gps.write(comando_inicio.encode('ascii'))
        print("GPS configurado. Inyectando correcciones en segundo plano...")

        # 2. Bucle ciego: Solo saca de la radio y mete en el GPS
        while True:
            if radio.in_waiting > 0:
                datos_rtk = radio.read(radio.in_waiting)
                gps.write(datos_rtk)
            
            # Pequeña pausa para no quemar el 100% del procesador
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nInyector detenido por el usuario.")
    except Exception as e:
        print(f"Error en los puertos: {e}")

if __name__ == '__main__':
    main()