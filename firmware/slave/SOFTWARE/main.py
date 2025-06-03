"""
Red Mesh LoRa - Nodo Esclavo con Sensores
==========================================

Este módulo implementa un nodo esclavo de la red mesh LoRa que recolecta
datos ambientales y de geolocalización para enviarlos al nodo maestro.

Características principales:
- Protocolo DSR (Dynamic Source Routing) para comunicación mesh
- Sensor de temperatura DS18B20 integrado
- Módulo GPS para geolocalización
- Respuesta automática a solicitudes de datos
- Configuración de hardware optimizada para ESP32

Sensores soportados:
- DS18B20: Sensor de temperatura digital de alta precisión
- GPS UART: Módulo GPS para coordenadas geográficas

Autores: Francisco Fernández & Nahuel Ontivero
Universidad: UTN - Facultad Regional Tucumán
Fecha: 2024
Licencia: MIT
"""

from machine import Pin, UART, Timer, RTC, SoftSPI # type: ignore
import time
from MicropyGPS import MicropyGPS # type: ignore
import onewire # type: ignore
import ds18x20 # type: ignore
from LoRa import LoRa # type: ignore
from DSRNode import DSRNode # type: ignore
from config import * # Importa todas las constantes de configuración

# ================================================================
# CONFIGURACIÓN DE HARDWARE
# ================================================================

# Configuración del módulo GPS usando constantes de config.py
modulo_gps = UART(GPS_UART_ID, baudrate=GPS_BAUDRATE, rx=GPS_RX_PIN)
gps = MicropyGPS(GPS_TIMEZONE)

# Configuración SPI para módulo LoRa usando constantes de config.py
spi = SoftSPI(baudrate=3000000, polarity=0, phase=0, 
              sck=Pin(SPI_SCK_PIN), mosi=Pin(SPI_MOSI_PIN), miso=Pin(SPI_MISO_PIN))
lora = LoRa(spi, cs_pin=Pin(LORA_CS_PIN), reset_pin=Pin(LORA_RST_PIN), dio0_pin=Pin(LORA_DIO0_PIN))

# Inicialización de temporizadores y RTC usando constantes de config.py
tim0 = Timer(TIMER_ID_DSR)      # Timer para DSR
tim1 = Timer(TIMER_ID_SENSORS)  # Timer para lecturas de sensores
tim2 = Timer(TIMER_ID_GPS)      # Timer para GPS
rtc = RTC()

# Crear nodo DSR usando constantes de config.py
nodo = DSRNode(NODE_ID, lora, rtc, tim0, qos=LORA_QOS)

# ================================================================
# CONFIGURACIÓN DE SENSORES
# ================================================================

# Configuración del sensor de temperatura DS18B20 usando constantes de config.py
ds_pin = Pin(DS18B20_PIN)  # Pin de datos del sensor de temperatura
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()  # Detectar sensores conectados

if not roms:
    print("⚠️ No se encontró ningún sensor DS18B20.")
else:
    print(f"✅ {len(roms)} sensor(es) DS18B20 encontrado(s)")

# ================================================================
# VARIABLES DE CONTROL DE TIEMPO
# ================================================================

ultimo_valor = 0                              # Timestamp de la última lectura
intervalo_valores = SENSOR_READ_INTERVAL      # Intervalo entre lecturas (desde config.py)

# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def convertir(secciones):
    """
    Convierte coordenadas GPS desde el formato DMS (grados, minutos, segundos)
    al formato decimal para facilitar su procesamiento y transmisión.
    
    Args:
        secciones (tuple): Tupla con (grados, minutos, dirección) del GPS
        
    Returns:
        str: Coordenada en formato decimal con 6 dígitos de precisión
        None: Si no hay datos GPS válidos
        
    Example:
        convertir((25, 30.5, 'S')) -> '-25.508333'
    """
    if secciones[0] == 0:  # secciones[0] contiene los grados
        return None
    
    # Convertir de grados y minutos a decimal
    data = secciones[0] + (secciones[1] / 60.0)  # secciones[1] contiene los minutos
    
    # Aplicar signo según la dirección
    if secciones[2] == 'S':  # Sur
        data = -data
    if secciones[2] == 'W':  # Oeste
        data = -data
        
    return '{0:.6f}'.format(data)  # 6 dígitos decimales de precisión

# Inicialización de variables globales
longitud_send = 0  # Valor por defecto
latitud_send = 0   # Valor por defecto

# Función para leer datos GPS y temperatura
def gps_y_temperatura(timer):
    # Lectura del GPS
    largo = modulo_gps.any()
    if largo > 0:
        b = modulo_gps.read(largo)
        for x in b:
            gps.update(chr(x))
    latitud = convertir(gps.latitude)
    longitud = convertir(gps.longitude)
    #print(f"GPS -> Longitud: {longitud}, Latitud: {latitud}")

    # Configuración de la fecha y hora del RTC
    actual_time = gps.timestamp
    actual_date = gps.date
    rtc = RTC()
    rtc.datetime((actual_date[2] + 2000, actual_date[1], actual_date[0], 0, actual_time[0], actual_time[1], int(actual_time[2]), 0))

    # Lectura del sensor de temperatura
    temp = None  # Valor por defecto
    if roms:
        ds_sensor.convert_temp()  # Inicia la conversión de temperatura
        time.sleep_ms(750)  # Esperar conversión
        for rom in roms:
            temp = ds_sensor.read_temp(rom)
    
    # Actualización de las variables globales
    global longitud_send, latitud_send
    if latitud is not None:  # Solo actualizar si hay un valor válido
        latitud_send = latitud
    if longitud is not None:  # Solo actualizar si hay un valor válido
        longitud_send = longitud

    # Creación del mensaje
    temp_str = str(temp)
    msg = f"{longitud_send}/{latitud_send}/{temp_str}"
    print(f"Mensaje: {msg}")

    nodo.update_sensor(msg)


def hello(timer):
    nodo.send_hello()


tim1.init(period=5000, mode=Timer.PERIODIC, callback=hello)


tim2.init(period=10000, mode=Timer.PERIODIC, callback=gps_y_temperatura)

while True:
    nodo.waiting_for_response()
    nodo.receive_message()
    time.sleep(1)



