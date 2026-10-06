# GPS RTK con UM980 — Proyecto PPS

Sistema de posicionamiento RTK (Real-Time Kinematic) basado en el módulo **UM980** de Unicore, compuesto por una **estación base**, un **rover** y un **nodo trazador** para ROS 2. El objetivo es lograr precisión centimétrica en la posición GPS del rover mediante la transmisión de correcciones RTCM3 por enlace de radio.

---

## Tabla de Contenidos

- [Arquitectura General](#arquitectura-general)
- [Hardware Necesario](#hardware-necesario)
- [Esquema de Conexiones](#esquema-de-conexiones)
- [Descripción de los Scripts](#descripción-de-los-scripts)
  - [Base.py](#basepy--estación-base)
  - [Rover.py](#roverpy--rover-receptor)
  - [Trazador.py](#trazadorpy--trazador-de-ruta-ros-2)
- [Instalación y Dependencias](#instalación-y-dependencias)
- [Uso](#uso)
- [Notas Importantes](#notas-importantes)

---

## Arquitectura General

El sistema se compone de tres etapas conectadas en serie:

1. **Estación Base:** El UM980 (configurado como base) genera correcciones RTCM3. `Base.py` lee esas correcciones por puerto serial y las envía a través de una radio transmisora.
2. **Rover:** La radio receptora recibe las correcciones RTCM3. `Rover.py` las lee y las inyecta en el puerto serial del UM980 rover, que las usa para calcular su posición con precisión centimétrica.
3. **Trazador (ROS 2):** Un driver NMEA (como `nmea_navsat_driver`) lee las sentencias NMEA del UM980 rover y publica los datos GPS en el tópico `/fix`. `Trazador.py` se suscribe a `/fix`, acumula los puntos y publica la ruta en `/ruta_seguida` para visualizarla en RViz2.

---

## Hardware Necesario

| Componente              | Cantidad | Descripción                                                   |
| ----------------------- | :------: | ------------------------------------------------------------- |
| Módulo GNSS **UM980**   |    2     | Uno para la base y otro para el rover                         |
| Radio transmisor/receptor (par) | 1 par | Cualquier par de radios seriales (ej: LoRa, HC-12, XBee, etc.) |
| Antena GNSS             |    2     | Antenas de buena calidad, idealmente de doble frecuencia      |
| Computadora / SBC       |    2     | Una por sitio (puede ser una Raspberry Pi, Jetson, PC, etc.)  |
| Cables USB-Serial       | 4 (mín.) | Para conectar los módulos UM980 y las radios a las computadoras |

---

## Esquema de Conexiones

### Estación Base

En la computadora de la base se conectan dos dispositivos por USB:

- **Puerto USB0** (`/dev/ttyUSB0` o `COMx`) → **UM980 (Base)** a 115200 baud. El UM980 debe estar configurado en modo base y emitir mensajes RTCM3 por este puerto.
- **Puerto USB1** (`/dev/ttyUSB1` o `COMx`) → **Radio TX** a 57600 baud. Conectar TX de la radio al pin RX del adaptador y RX de la radio al pin TX del adaptador.

> **Configuración previa del UM980 (Base):** Usando UPrecise o comandos AT por terminal, se debe:
> 1. Configurar el módulo como **Base** estática (`mode base time 60` o `mode base <lat> <lon> <alt>`).
> 2. Habilitar la salida de mensajes **RTCM3** por el puerto COM correspondiente (ej: `rtcm1005 com1 10`, `rtcm1077 com1 1`, etc.).

### Rover

En la computadora del rover se conectan dos dispositivos por USB:

- **Puerto USB0** (`/dev/ttyUSB0` o `COMx`) → **Radio RX** a 57600 baud. Recibe las correcciones RTCM3 de la base.
- **Puerto USB1** (`/dev/ttyUSB1` o `COMx`) → **UM980 (Rover)** a 115200 baud. El script inyecta las correcciones RTCM3 aquí y envía los comandos de configuración al inicio.

> **Configuración previa del UM980 (Rover):** El script `Rover.py` envía automáticamente los comandos iniciales:
> - `unlog` — Detiene cualquier log previo.
> - `mode rover` — Configura el módulo como rover RTK.
> - `gngga com1 0.1` — Solicita la sentencia GGA cada 0.1 segundos.

### Nodo ROS 2 (Trazador)

En la misma computadora del rover, dentro de ROS 2:

- **`nmea_navsat_driver`** (u otro driver NMEA) lee el puerto serial del UM980 y publica los datos GPS en el tópico `/fix` (tipo `NavSatFix`).
- **`Trazador.py`** se suscribe a `/fix`, acumula los puntos GPS y publica la ruta completa en `/ruta_seguida` (tipo `Path`), visualizable con RViz2.

---

## Descripción de los Scripts

### `Base.py` — Estación Base

**Propósito:** Lee las correcciones RTCM3 generadas por el UM980 configurado como base y las retransmite por radio serial al rover.

**Funcionamiento:**
1. Abre dos puertos seriales: uno para el GPS (UM980) y otro para la radio transmisora.
2. En un bucle continuo, lee todos los bytes disponibles del UM980.
3. Escribe esos bytes directamente en el puerto de la radio.
4. Este proceso es transparente: no interpreta los datos RTCM, solo los redirige.

**Parámetros configurables:**
- `PUERTO_GPS_BASE` — Puerto serial del UM980 (default: `/dev/ttyUSB0`).
- `PUERTO_RADIO_BASE` — Puerto serial de la radio TX (default: `/dev/ttyUSB1`).
- `BAUD_GPS` — Baudrate del GPS: `115200`.
- `BAUD_RADIO` — Baudrate de la radio: `57600`.

---

### `Rover.py` — Rover Receptor

**Propósito:** Recibe las correcciones RTCM3 por radio e inyecta los datos crudos directamente en el puerto serial del UM980 rover, para que este calcule su posición con precisión centimétrica.

**Funcionamiento:**
1. Abre el puerto de la radio receptora y el del UM980.
2. Envía comandos iniciales al UM980 para configurarlo como rover (`mode rover`) y solicitar sentencias GGA.
3. En un bucle continuo, lee los datos que llegan por radio y los escribe en el puerto del GPS.
4. Es un "inyector ciego": no valida ni parsea los datos RTCM, simplemente los redirige.

**Parámetros configurables:**
- `PUERTO_RADIO` — Puerto serial de la radio RX (default: `/dev/ttyUSB0`).
- `PUERTO_GPS` — Puerto serial del UM980 rover (default: `/dev/ttyUSB1`).

---

### `Trazador.py` — Trazador de Ruta (ROS 2)

**Propósito:** Nodo de ROS 2 que se suscribe al tópico `/fix` (publicado por un driver NMEA como `nmea_navsat_driver`) y acumula las posiciones GPS recibidas en un mensaje de tipo `Path`, publicándolo en `/ruta_seguida` para su visualización en RViz2.

**Funcionamiento:**
1. Se suscribe al tópico `/fix` de tipo `NavSatFix`.
2. Cada vez que recibe una lectura con señal válida (`status >= 0`), crea un `PoseStamped` usando latitud como `x` y longitud como `y`.
3. Agrega el punto a la ruta acumulada y publica el `Path` completo en `/ruta_seguida`.

**Tópicos:**
| Tópico           | Tipo         | Dirección   | Descripción                           |
| ---------------- | ------------ | ----------- | ------------------------------------- |
| `/fix`           | `NavSatFix`  | Suscripción | Datos GPS del rover                   |
| `/ruta_seguida`  | `Path`       | Publicación | Ruta acumulada de todas las posiciones |

---

## Instalación y Dependencias

### Python (Base y Rover)

```bash
pip install pyserial
```

### ROS 2 (Trazador)

Requiere un workspace de ROS 2 (Humble, Iron o Jazzy) con los siguientes paquetes:

```bash
sudo apt install ros-<distro>-nmea-navsat-driver
```

Dependencias Python de ROS 2:
- `rclpy`
- `sensor_msgs`
- `nav_msgs`
- `geometry_msgs`

---

## Uso

### 1. Iniciar la Base

```bash
# En la computadora de la base
python3 Base.py
```

### 2. Iniciar el Rover

```bash
# En la computadora del rover
python3 Rover.py
```

### 3. Iniciar el driver NMEA y el Trazador (ROS 2)

```bash
# Terminal 1: Driver GPS → publica /fix
ros2 launch nmea_navsat_driver nmea_serial_driver.launch.py

# Terminal 2: Trazador de ruta
ros2 run <nombre_paquete> Trazador

# Terminal 3 (opcional): Visualizar en RViz2
rviz2
# Agregar un display de tipo "Path" apuntando al tópico /ruta_seguida
```

---

## Notas Importantes

1. **Puertos seriales:** Los nombres de los puertos (`/dev/ttyUSBx`) varían según el sistema operativo y el orden en que se conectan los dispositivos. En **Windows** se usan `COMx` (ej: `COM4`, `COM5`). Verificar con `ls /dev/ttyUSB*` (Linux) o el Administrador de Dispositivos (Windows).

2. **Baudrates:** Ambos extremos (base y rover) deben usar los mismos baudrates para la radio. El baudrate del GPS (115200) es el default del UM980.

3. **Configuración del UM980:** Antes de ejecutar los scripts, el UM980 de la base debe estar configurado para emitir RTCM3. Esto se hace **una sola vez** con el software **UPrecise** o enviando comandos por terminal serial.

4. **Alcance de la radio:** La distancia máxima entre base y rover depende del tipo de radio. Radios LoRa pueden alcanzar varios kilómetros; módulos HC-12 unos cientos de metros.

5. **Precisión RTK:** La solución RTK (tipo "Fix") puede tardar algunos minutos en converger. Mientras converge, el GPS reportará solución "Float" con precisión intermedia.

6. **Trazador — uso de lat/lon como x/y:** El nodo `Trazador.py` usa directamente latitud y longitud como coordenadas `x` e `y` del `PoseStamped`. Esto es una simplificación para visualización rápida en 2D. Para aplicaciones reales de navegación se debería usar una proyección UTM o un frame `earth`.
