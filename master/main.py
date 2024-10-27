import time
from machine import SPI, Pin
from LoRa import LoRa
from DSRNode import DSRNode
import json


spi = SPI(1, baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19)) 
lora = LoRa(spi, cs_pin=5, reset_pin=4, dio0_pin=2)

node = DSRNode("Pancho",lora)

while True:
    """
    node.send_hello()
    time.sleep(5)
    """
    node.broadcast_rreq("Morty")
    time.sleep(5)
    node.receive_message()
    time.sleep(5)
