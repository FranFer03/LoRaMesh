import sys
import time

def main():
    while True:
        try:
            comando = sys.stdin.readline().strip()  # Intentar leer un comando
            if comando:
                #print(f"Comando recibido: {comando}")   # Imprimir en sys.stdout (se envía por el puerto USB)
            
                if comando == 'REDES':
                    print('Código prueba REDES')
                elif comando == 'CAMINOS':
                    print('Código prueba CAMINOS')
                elif comando == 'PAQUETE':
                    print('Código prueba PAQUETE')
                elif comando == 'SINCRONIZAR':
                    print('Código prueba SINCRONIZAR')
                else:
                    print('Comando no reconocido')

        except Exception as e:
            pass  # No hacer nada si no hay datos

        time.sleep(0.1)

main()
