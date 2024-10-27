import time
from machine import SPI, Pin , Timer
from LoRa import LoRa
from DSRNode import DSRNode
import json

simulated_unix_time = 203203023

spi = SPI(1, baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19)) 
lora = LoRa(spi, cs_pin=5, reset_pin=4, dio0_pin=2)

node = DSRNode("Pancho",lora)

def display_time():
    global simulated_unix_time
    simulated_unix_time += 1

timer = Timer(0)
timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: display_time())

while True:
    """
    node.send_hello()
    time.sleep(5)
    """
    node.broadcast_rreq("Morty")
    time.sleep(5)
    node.receive_message()
    time.sleep(5)
