import machine
import onewire
import ds18x20
import time

# Configurar el pin GPIO donde conectaste el DS18B20
ds_pin = machine.Pin(12)  # Cambia "4" por el GPIO que estés usando en la ESP32
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# Escanear dispositivos en el bus 1-Wire
roms = ds_sensor.scan()
print("Dispositivo encontrado")

if not roms:
    print("No se encontraron sensores. Verifica la conexión.")

while roms:
    ds_sensor.convert_temp()  # Iniciar la conversión de temperatura
    time.sleep_ms(750)  # Esperar la conversión (750 ms para el DS18B20 a 12 bits)

    for rom in roms:
        temp = ds_sensor.read_temp(rom)  # Leer la temperatura
        if temp is not None:
            print(f"Temperatura del sensor de nodo: {temp:.2f} °C")
        else:
            print(f"Error al leer el sensor {rom}")
    
    time.sleep(2)  # Tiempo entre lecturas
