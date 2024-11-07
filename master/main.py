import time
from machine import Pin, Timer, SoftSPI, SoftI2C, RTC
from LoRa import LoRa
import json
from DSRNode import DSRNode


spi = SoftSPI(baudrate=3000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(18), reset_pin=Pin(14), dio0_pin=Pin(26))

tim1 = Timer(0)
rtc = RTC()
#rtc.datetime((2024, 11, 7, 27, 34, 0, 0, 0))
print(rtc.datetime())
nodo = DSRNode("B", lora, rtc, tim1, qos=-80, role="master")

def periodico(timer):
    pass
    
tim1 = Timer(1)
tim1.init(period=10000, mode=Timer.PERIODIC ,callback=periodico)

while True:
    nodo.receive_message()