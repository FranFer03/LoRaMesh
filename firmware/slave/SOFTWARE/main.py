from machine import Pin, UART, Timer, RTC, SoftSPI # type: ignore
import time
from MicropyGPS import MicropyGPS # type: ignore
import onewire # type: ignore
import ds18x20 # type: ignore
from LoRa import LoRa # type: ignore
from DSRNode import DSRNode # type: ignore

# Configuración del módulo GPS
modulo_gps = UART(2, baudrate=9600, rx=16)
Zona_Horaria = -3
gps = MicropyGPS(Zona_Horaria)

spi = SoftSPI(baudrate=3000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(18), reset_pin=Pin(14), dio0_pin=Pin(26))

tim0 = Timer(0)
tim1 = Timer(1)
tim2 = Timer(2)
rtc = RTC()

nodo = DSRNode("C", lora, rtc, tim0, qos=-90)

# Configuración del sensor de temperatura DS18B20
ds_pin = Pin(12)  # Pin de datos del sensor de temperatura
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()  # Detectar sensores conectados
if not roms:
    print("No se encontró ningún sensor DS18B20.")
else:
    print("Sensores DS18B20 encontrado")

# Variables de tiempo
ultimo_valor = 0
intervalo_valores = 30




# Función para convertir datos GPS
def convertir(secciones):
    if secciones[0] == 0:  # secciones[0] contiene los grados
        return None
    data = secciones[0] + (secciones[1] / 60.0)  # secciones[1] contiene los minutos
    if secciones[2] == 'S':
        data = -data
    if secciones[2] == 'W':
        data = -data
    return '{0:.6f}'.format(data)  # 6 dígitos decimales

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



