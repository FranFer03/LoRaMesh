import time

# Almacena el tiempo de inicio
inicio = time.time()

def main():
    while True:
        # Simulando la lectura de comando por consola
        comando = input("Introduce comando: ").strip()
        
        if comando == "TIEMPO":
            # Calcula los segundos transcurridos
            tiempo_transcurrido = time.time() - inicio
            print(f"Segundos desde que inició el programa: {int(tiempo_transcurrido)} s")
        
        time.sleep(1)  # Esperar un segundo para reducir la carga de la CPU

main()
