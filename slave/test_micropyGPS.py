from machine import Pin
import time
from cgps import GPS


gps_module = GPS(uart_port=2, baudrate=9600, timezone_offset=-3)

while True:
    location_data = gps_module.give_location()
    unix_time, latitude, longitude = location_data
    print("Unix Time:", unix_time, "Latitude:", latitude, "Longitude:", longitude)
    time.sleep(1)
