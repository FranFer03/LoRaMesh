from machine import Pin, UART, Timer, RTC
import time

from MicropyGPS import MicropyGPS        # https://github.com/inmcm/micropyGPS

modulo_gps = UART(1, baudrate=9600, tx=10, rx=9)

Zona_Horaria = -3
gps = MicropyGPS(Zona_Horaria)




ultimo_valor = 0
intervalo_valores = 30

def convertir(secciones):
    if (secciones[0] == 0): # secciones[0] contiene los grados
        return None
    # secciones[1] contiene los minutos    
    data = secciones[0]+(secciones[1]/60.0)
    # secciones[2] contiene 'E', 'W', 'N', 'S'
    if (secciones[2] == 'S'):
        data = -data
    if (secciones[2] == 'W'):
        data = -data

    data = '{0:.6f}'.format(data) # 6 digitos decimales
    return str(data)

def gps_data(timer):
    
    largo = modulo_gps.any()
    if largo > 0:
        b = modulo_gps.read(largo)
        for x in b:
            msg = gps.update(chr(x))
    
    
    latitud = convertir(gps.latitude)
    longitud = convertir(gps.longitude)
    print(longitud, latitud)
     
    actual_time = gps.timestamp
    actual_date = gps.date
    rtc = RTC()
    rtc.datetime((actual_date[2]+2000, actual_date[1], actual_date[0], 0,actual_time[0], actual_time[1], int(actual_time[2]), 0))


tim0 = Timer(2)
tim0.init(period=1000, mode=Timer.PERIODIC, callback=gps_data)

rtc = RTC()

while True:
    msg = rtc.datetime()
    print(msg)
    time.sleep(1)