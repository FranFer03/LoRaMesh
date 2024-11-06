import time
from machine import Pin , Timer, SoftSPI
from LoRa import LoRa
#from DSRNode import DSRNode
import json

simulated_unix_time = 203203023
"""
spi = SPI(1, baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19)) 
lora = LoRa(spi, cs_pin=5, reset_pin=4, dio0_pin=2)

node = DSRNode("Pancho",lora,timestamp=simulated_unix_time)

def display_time():
    global simulated_unix_time
    simulated_unix_time += 1

timer = Timer(0)
timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: display_time())
"""
device_config = {
    'miso':19,
    'mosi':23,
    'ss':5,
    'sck':18,
    'dio_0':26,
    'reset':36,
}

spi = SoftSPI(baudrate=3000000, polarity=1, phase=0, sck=Pin(5), mosi=Pin(27), miso=Pin(19)) 
lora = LoRa(spi, cs_pin=18,reset_pin=14,  dio0_pin=26)

while True:
    lora.send("Hola")
    time.sleep(5)
    
