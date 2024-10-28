from DSRNode import DSRNode
import time
from machine import SPI, Pin, Timer
from LoRa import LoRa
import json

simulated_unix_time = 203203023

def display_time():
    global simulated_unix_time
    simulated_unix_time += 1

spi = SPI(1, baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19)) 
lora = LoRa(spi, cs_pin=5, reset_pin=4, dio0_pin=2)
node = DSRNode("Morty",lora, -100, timestamp = simulated_unix_time)

timer = Timer(0)
timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: display_time())

while True:
    node.broadcast_rreq("Pancho")
    node.receive_message()
    time.sleep(1)
    node.set_timestamp(simulated_unix_time)