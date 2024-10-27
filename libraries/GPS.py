from machine import Pin, UART, I2C
import utime, time
from MicropyGPS import MicropyGPS

modulo_gps = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

Zona_Horaria = -3
gps = MicropyGPS(Zona_Horaria)

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

def location():
    time.sleep_ms(5000)
    largo = modulo_gps.any()
    if largo > 0:
        b = modulo_gps.read(largo)
        for x in b:
            msg = gps.update(chr(x))
    
    latitud = convertir(gps.latitude)
    longitud = convertir(gps.longitude)
    
    if (latitud == None or longitud == None):
        print("Datos no")
        print("disponibles")
    
    t = gps.timestamp
    horario = '{:02d}:{:02d}:{:02}'.format(t[0], t[1], t[2])
    print('Satelites: ' + str(gps.satellites_in_use))
    print('Lat:'+ latitud)
    print('Lon:'+ longitud)
    print('Horario:'+ horario)