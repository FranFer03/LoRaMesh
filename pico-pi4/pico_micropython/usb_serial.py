import sys
import time
import ujson

# Definir el diccionario de datos
query = {'RREP': [], 'RREQ': [['784317687', 'A', 'B'], ['784317689', 'A', 'B']], 'DATA': [], 'RESP': []}

def main():
    while True:
        try:
            comando = sys.stdin.readline().strip()  # Intentar leer un comando
            if comando:
                if comando == 'RUTAS':
                    print('Código prueba REDES')
                elif comando == 'CAMINOS':
                    print('Código prueba CAMINOS')
                elif comando == 'PAQUETE':
                    print('Código prueba PAQUETE')
                elif comando == 'DATOS':
                    print('Código prueba SINCRONIZAR')
                elif comando == 'ENVIAR_QUERY':
                    # Convertir `query` a JSON y enviarlo por USB
                    query_json = ujson.dumps(query)
                    print(query_json)  # Esto envía los daZtos al puerto USB
                    #print("Datos enviados a través del puerto USB")

                else:
                    print('Comando no reconocido')

        except Exception as e:
            print("Error:", e)

        time.sleep(0.1)

main()
