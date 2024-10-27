from machine import Pin, UART, I2C
import time
from MicropyGPS import MicropyGPS
from cgps import GPS

# Inicializar UART para el módulo GPS
gps_uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))

# Definir zona horaria e instancia de GPS
timezone_offset = -3
gps_data = MicropyGPS(timezone_offset)
gps_module = GPS(gps_data)

while True:
    unix_time, latitude, longitude = gps_module.give_location()
    print("Unix Time:", unix_time, "Latitude:", latitude, "Longitude:", longitude)
    time.sleep(1)
