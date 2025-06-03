"""
DSR Node - Implementación del Protocolo Dynamic Source Routing
==============================================================

Este módulo implementa el protocolo DSR (Dynamic Source Routing) para redes mesh
usando tecnología LoRa como medio de transmisión. Incluye funcionalidades para:

- Descubrimiento automático de rutas (RREQ/RREP)
- Transmisión confiable de datos (DATA/RESP)
- Mantenimiento de rutas y detección de fallos
- Gestión de caché y limpieza automática
- Control de calidad de servicio (QoS)

Autores: Francisco Fernández & Nahuel Ontivero
Universidad: UTN - Facultad Regional Tucumán
"""

import time
import random
from machine import Timer # type: ignore
from config import DSR_TIMEOUT, DSR_RETRY_INTERVAL, DSR_MAX_ATTEMPTS, DSR_CACHE_TIMEOUT

class DSRNode:
    """
    Implementa un nodo para una red mesh basada en el protocolo DSR (Dynamic Source Routing)
    usando LoRa como medio de comunicación.
    
    El protocolo DSR es un protocolo de enrutamiento reactivo que descubre rutas
    bajo demanda y mantiene un caché de rutas conocidas. Cada nodo mantiene
    información sobre rutas hacia otros nodos y puede actuar como reenviador
    de mensajes.
    
    Attributes:
        MAX_ATTEMPTS (int): Número máximo de reintentos para envío de datos
        RETRY_INTERVAL (int): Intervalo entre reintentos en segundos
        TIMEOUT (int): Tiempo máximo de espera para respuestas en segundos
        CACHE_TIMEOUT (int): Tiempo de vida de entradas en caché en segundos
    """
      # ================================================================
    # CONSTANTES DEL PROTOCOLO DSR
    # ================================================================
    
    # Las constantes ahora se importan desde config.py para centralizar configuración
    MAX_ATTEMPTS = DSR_MAX_ATTEMPTS        # Máximo número de reintentos
    RETRY_INTERVAL = DSR_RETRY_INTERVAL    # Intervalo entre reintentos (segundos)
    TIMEOUT = DSR_TIMEOUT                  # Timeout para respuestas (segundos)
    CACHE_TIMEOUT = DSR_CACHE_TIMEOUT      # Tiempo de vida del caché (segundos)

    def __init__(self, node_id, lora, rtc, timer, qos=-80, role="slave"):
        """
        Inicializa el nodo DSR con los parámetros necesarios.
        
        Args:
            node_id (str/int): Identificador único del nodo en la red
            lora (LoRa): Instancia del módulo LoRa para comunicación
            rtc (RTC): Reloj de tiempo real para timestamps
            timer (Timer): Temporizador para operaciones periódicas
            qos (int, optional): Umbral RSSI para calidad de señal. Defaults to -80.
            role (str, optional): Rol del nodo ("master" o "slave"). Defaults to "slave".
        
        Note:
            El node_id debe ser único en toda la red mesh para evitar conflictos
            de enrutamiento. Se recomienda usar valores alfanuméricos cortos.
        """
        # ================================================================
        # ESTRUCTURAS DE DATOS PRINCIPALES
        # ================================================================
        
        self.neighbors = set()          # Conjunto de nodos vecinos detectados
        self.rreq_id = 0               # ID incremental para solicitudes RREQ
        self.routes = {}               # Tabla de enrutamiento: {destino: [ruta]}
        
        # Caché de mensajes procesados para evitar duplicados
        self.query = {
            "RREQ": [],  # Route Requests procesados: [id, source, dest]
            "RREP": [],  # Route Replies procesados: [id, source, dest]  
            "DATA": [],  # Data messages procesados: [id, source, dest]
            "RESP": []   # Response messages procesados: [id, source, dest]
        }
        
        # ================================================================
        # CONFIGURACIÓN DEL NODO
        # ================================================================
        
        self.node_id = node_id                # ID único del nodo
        self.quality_neighbor = qos           # Umbral RSSI para vecinos
        self.lora = lora                     # Instancia LoRa
        self.rtc = rtc                       # Reloj tiempo real
        self.timer = timer                   # Temporizador
        self.role = role                     # Rol en la red
        
        # ================================================================
        # CONTROL DE RESPUESTAS Y REINTENTOS
        # ================================================================
        
        self.waiting_response = False         # Flag: esperando respuesta
        self.response_timer = 0              # Timer para control de timeout
        self.attempts = 0                    # Contador de intentos actuales
        self.sent_message = None             # Último mensaje enviado (para reintento)
        self.timestamp_message = 0           # Timestamp actual del nodo

        # Inicializa el temporizador para actualizar timestamp y limpiar caché
        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.set_timestamp)

        print(f"Node {self.node_id} is operating as {self.role}.")

    def set_timestamp(self, timer):
        """
        Actualiza el timestamp del nodo usando el RTC y limpia la caché de mensajes antiguos.
        
        Esta función es llamada periódicamente por el temporizador para:
        - Mantener sincronizado el timestamp interno
        - Limpiar mensajes antiguos del caché
        - Proveer timestamps únicos para nuevos mensajes
        
        Args:
            timer: Objeto Timer que ejecuta esta función (callback)
        """
        try:
            rtc_time = self.rtc.datetime()
            # Convertir tiempo RTC a timestamp Unix
            t = (rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[4], rtc_time[5], rtc_time[6], 0, 0, 0)
            self.timestamp_message = time.mktime(t)
            
            # Limpiar caché de mensajes antiguos
            self.cache_cleaning()
        except Exception as e:
            print(f"Error en set_timestamp: {e}")

    def remove_query(self, command, element):
        """
        Elimina un elemento específico de la lista de consultas (query) para un comando dado.
        
        Útil para limpiar manualmente entradas específicas del caché cuando se detectan
        inconsistencias o para forzar el reprocesamiento de ciertos mensajes.
        
        Args:
            command (str): Comando del cual eliminar ("RREQ", "RREP", "DATA", "RESP")
            element: Elemento a buscar y eliminar de la lista
            
        Example:
            remove_query("RREQ", "12345")  # Elimina RREQ con ID 12345
        """
        try:
            initial_len = len(self.query[command])
            self.query[command] = [sublist for sublist in self.query[command] if element not in sublist]
            
            if len(self.query[command]) < initial_len:
                print(f"✓ Elemento '{element}' eliminado del comando '{command}'")
            else:
                print(f"⚠ Elemento '{element}' no encontrado en comando '{command}'")
        except KeyError:
            print(f"✗ Comando '{command}' no existe en el diccionario")
        except Exception as e:
            print(f"✗ Error eliminando elemento: {e}")
    
    def cache_cleaning(self):
        """
        Elimina mensajes antiguos de la caché según el tiempo de expiración definido.
        
        Esta función es esencial para:
        - Evitar que la memoria se llene con mensajes antiguos
        - Permitir reprocesamiento de rutas que pueden haber cambiado
        - Mantener la eficiencia del sistema
        
        Los mensajes más antiguos que CACHE_TIMEOUT segundos son eliminados.
        """
        try:
            current_time = self.timestamp_message
            for cmd in ["RREQ", "RREP", "DATA", "RESP"]:
                original_count = len(self.query[cmd])
                self.query[cmd] = [
                    entry for entry in self.query[cmd] 
                    if current_time - int(entry[0]) < self.CACHE_TIMEOUT
                ]
                cleaned_count = original_count - len(self.query[cmd])
                if cleaned_count > 0:
                    print(f"🧹 Limpiadas {cleaned_count} entradas antiguas de {cmd}")
        except Exception as e:
            print(f"✗ Error en limpieza de caché: {e}")

    def calculate_checksum(self, message):
        """
        Calcula un checksum simple para verificar la integridad de los mensajes.
        
        Implementa un algoritmo de suma de verificación de 16 bits que:
        - Procesa el mensaje en pares de bytes
        - Acumula la suma con manejo de overflow
        - Retorna el complemento a uno del resultado
        
        Args:
            message (str): Mensaje para el cual calcular checksum
            
        Returns:
            int: Checksum de 16 bits del mensaje
            
        Note:
            Este checksum detecta errores de transmisión básicos pero no
            es criptográficamente seguro.
        """
        try:
            message_bytes = message.encode('utf-8')
            checksum = 0
            
            # Procesar en pares de bytes
            for i in range(0, len(message_bytes), 2):
                word = message_bytes[i]
                if i + 1 < len(message_bytes):
                    word = (word << 8) + message_bytes[i + 1]
                
                checksum += word
                # Manejar overflow de 16 bits
                checksum = (checksum & 0xFFFF) + (checksum >> 16)
            
            # Retornar complemento a uno
            return ~checksum & 0xFFFF
        except Exception as e:
            print(f"✗ Error calculando checksum: {e}")
            return 0

    def verify_checksum(self, message_with_checksum):
        """
        Verifica que el checksum de un mensaje recibido sea correcto.
        
        Separa el mensaje del checksum, recalcula el checksum del mensaje
        y lo compara con el recibido para verificar integridad.
        
        Args:
            message_with_checksum (str): Mensaje con checksum al final (formato: "mensaje:checksum")
            
        Returns:
            bool: True si el checksum es válido, False en caso contrario
            
        Example:
            verify_checksum("RESP:A:B:123:ruta:datos:45678")  # True si checksum válido
        """
        try:
            # Separar mensaje y checksum
            *message_parts, received_checksum = message_with_checksum.rsplit(":", 1)
            message = ":".join(message_parts)
            
            # Calcular checksum esperado
            calculated_checksum = self.calculate_checksum(message)
            
            # Comparar checksums
            return int(received_checksum) == calculated_checksum
        except Exception as e:
            print(f"✗ Error verificando checksum: {e}")
            return False

    def send_hello(self):
        """
        Envía un mensaje HELLO para anunciar la presencia del nodo a sus vecinos.
        
        Los mensajes HELLO son la base del descubrimiento de vecinos en DSR:
        - Se envían periódicamente
        - Permiten que otros nodos detecten este nodo como vecino
        - No requieren respuesta (broadcast unidireccional)
        
        Format: "HELLO:{node_id}"
        """
        try:
            hello_message = f"HELLO:{self.node_id}"
            self.lora.send(hello_message)
            print(f"📡 HELLO enviado desde nodo {self.node_id}")
        except Exception as e:
            print(f"✗ Error enviando HELLO: {e}")
    
    def send_response(self, destination, id_response, routelist):
        """
        Envía una respuesta RESP con datos simulados de sensores.
        
        Esta función genera datos simulados de sensores y los envía como respuesta
        a una solicitud DATA. En una implementación real, aquí se leerían
        sensores reales conectados al nodo.
        
        Args:
            destination (str): Nodo destino de la respuesta
            id_response (str): ID de la solicitud original (para correlación)
            routelist (str): Ruta a seguir para llegar al destino
            
        Format: "RESP:{source}:{dest}:{id}:{route}:{sensor_data}:{checksum}"
        """
        try:
            # Generar datos simulados de sensores
            temp = round(random.uniform(15.0, 35.0), 1)      # Temperatura 15-35°C
            humidity = round(random.uniform(30.0, 90.0), 1)   # Humedad 30-90%
            
            # Construir mensaje sin checksum
            data_message_raw = f"RESP:{self.node_id}:{destination}:{id_response}:{routelist}:{temp},{humidity}"
            
            # Calcular y agregar checksum
            checksum = self.calculate_checksum(data_message_raw)
            data_message = f"{data_message_raw}:{checksum}"
            
            # Enviar respuesta
            self.lora.send(data_message)
            print(f"📤 RESP enviado a {destination}: temp={temp}°C, hum={humidity}%")
        except Exception as e:
            print(f"✗ Error enviando respuesta: {e}")

    def broadcast_rreq(self, destination):
        """
        Difunde un mensaje RREQ para descubrir rutas hacia un destino.
        
        Este es el mecanismo principal de descubrimiento de rutas en DSR:
        - Crea un RREQ único con timestamp como ID
        - Lo difunde a todos los vecinos
        - Cada nodo intermedio agregará su ID a la ruta
        - El destino responderá con RREP
        
        Args:
            destination (str): Nodo destino para el cual buscar ruta
            
        Format: "RREQ:{source}:{dest}:{rreq_id}:{route}"
        """
        try:
            # Usar timestamp como ID único para la solicitud
            self.rreq_id = self.timestamp_message
            
            # Crear mensaje RREQ inicial (ruta vacía)
            rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}:"
            
            # Registrar en caché para evitar reprocessar
            self.query["RREQ"].append([str(self.rreq_id), self.node_id, destination])
            
            # Enviar broadcast
            self.lora.send(rreq_message)
            print(f"🔍 RREQ broadcast para destino {destination} (ID: {self.rreq_id})")
        except Exception as e:
            print(f"✗ Error enviando RREQ: {e}")

    def send_rrep(self, destination, id_message, routes):
        """
        Envía un mensaje RREP con la ruta descubierta hacia el destino.
        
        Los mensajes RREP son la respuesta a los RREQ y contienen:
        - La ruta completa desde el origen hasta el destino
        - El ID de la solicitud original (para correlación)
        - Se envían usando la ruta inversa del RREQ
        
        Args:
            destination (str): Nodo que inició la búsqueda de ruta
            id_message (str): ID del RREQ original
            routes (list): Lista de nodos que forman la ruta
            
        Format: "RREP:{source}:{dest}:{id}:{route}"
        """
        try:
            # Construir mensaje RREP
            rrep_message = f"RREP:{self.node_id}:{destination}:{id_message}:{'-'.join(routes)}"
            
            # Registrar en caché
            self.query["RREP"].append([id_message, self.node_id, destination])
            
            # Enviar RREP
            self.lora.send(rrep_message)
            print(f"↩️ RREP enviado a {destination} con ruta: {routes}")
        except Exception as e:
            print(f"✗ Error enviando RREP: {e}")
    
    def request_data(self, destination):
        """
        Solicita datos a un nodo destino usando la ruta conocida.
        Si no hay ruta disponible, inicia el descubrimiento de ruta.
        
        Esta función implementa la lógica principal para solicitar datos:
        1. Verifica si existe una ruta hacia el destino
        2. Si existe, envía DATA por esa ruta
        3. Si no existe, inicia descubrimiento con RREQ
        4. Configura timers para reintentos y timeouts
        
        Args:
            destination (str): Nodo del cual solicitar datos
            
        Note:
            Después de enviar DATA, el nodo esperará RESP con timeout
        """
        try:
            if destination in self.routes.keys():
                # Ruta disponible - enviar solicitud directamente
                route = self.routes[destination]
                print(f"📨 Enviando solicitud de datos a {destination} via {route}")
                
                # Construir mensaje DATA
                data_message = f"DATA:{self.node_id}:{destination}:{self.timestamp_message}:{'-'.join(route)}"
                
                # Registrar solicitud en caché
                self.query["DATA"].append([str(self.timestamp_message), self.node_id, destination])
                
                # Enviar mensaje
                self.lora.send(data_message)
                
                # Configurar control de respuesta
                self.waiting_response = True
                self.response_timer = time.time()
                self.attempts = 1
                self.sent_message = data_message
                
            else:
                # No hay ruta - iniciar descubrimiento
                print(f"🔍 No hay ruta a {destination}, iniciando descubrimiento...")
                self.broadcast_rreq(destination)
                
        except Exception as e:
            print(f"✗ Error solicitando datos: {e}")

    def waiting_for_response(self):
        """
        Espera la respuesta a una solicitud de datos, reintentando si es necesario.
        Marca la ruta como caída si no hay respuesta tras varios intentos.
        Incluye control de errores robusto.
        """
        if self.waiting_response:
            try:
                current_time = time.time()
                time_elapsed = current_time - self.response_timer

                if time_elapsed >= self.RETRY_INTERVAL and self.attempts < self.MAX_ATTEMPTS:
                    self.response_timer = current_time
                    try:
                        _, resource, redestination, redata_id, reroutelist = self.sent_message.split(":")
                        self.query["DATA"][-1][0] = str(self.timestamp_message)
                        data_message = f"DATA:{resource}:{redestination}:{self.timestamp_message}:{'-'.join(self.routes[redestination])}"
                        self.lora.send(data_message)
                        self.attempts += 1
                        print(f"{self.node_id} reenviando mensaje de solicitud de datos {self.query['DATA'][-1][0]}")
                    except Exception as e:
                        print(f"Error al reconstruir y reenviar DATA: {e}")

                # Verificar si se ha recibido un paquete
                try:
                    if self.lora.is_packet_received():
                        message = self.lora.get_packet(rssi=True)
                        payload = message.get('payload')
                        if payload.startswith("RESP"):
                            if self.verify_checksum(payload):
                                try:
                                    sequence, source, destination, data_id, routelist, sensors_data, checksum = payload.split(":")
                                    if destination == self.node_id and data_id == self.query["DATA"][-1][0]:
                                        if not [data_id, source, destination] in self.query["RESP"]:
                                            self.query["RESP"].append([data_id, source, destination])
                                            print(f"{self.node_id} recibió respuesta de la petición {data_id} con los datos {sensors_data}")
                                            self.waiting_response = False
                                            return payload
                                except Exception as e:
                                    print(f"Error al procesar RESP recibido: {e}")
                            else:
                                print(f"{self.node_id} no recibió un checksum correcto")
                except Exception as e:
                    print(f"Error al verificar o procesar paquete recibido: {e}")

                if time_elapsed > self.TIMEOUT:
                    print(f"{self.node_id} no recibió respuesta para la petición {self.query['DATA'][-1][0]} por lo tanto la ruta está caída")
                    self.waiting_response = False
                    try:
                        self.routes.pop(self.query["DATA"][0][2])
                    except Exception as e:
                        print(f"Error al eliminar ruta caída: {e}")
                    print(self.routes)
            except Exception as e:
                print(f"Error general en waiting_for_response: {e}")
        else:
            return None

    def receive_message(self):
        """
        Escucha la red y procesa los mensajes recibidos según el tipo de mensaje (HELLO, RREQ, RREP, DATA, RESP).
        """
        try:
            if self.lora.is_packet_received():
                message = self.lora.get_packet(rssi=True)
                payload = message.get('payload', '')
                if payload.startswith("HELLO"):
                    self.process_hello(message)
                elif payload.startswith("RREQ"):
                    self.process_rreq(message)
                elif payload.startswith("RREP"):
                    self.process_rrep(payload)
                elif payload.startswith("DATA"):
                    self.process_data(message)
                elif payload.startswith("RESP"):
                    self.process_response(message)
        except Exception as e:
            print(f"Error al recibir mensaje: {e}")

    def process_hello(self, message):
        """
        Procesa un mensaje HELLO recibido y agrega al nodo a la lista de vecinos si cumple con el RSSI.
        """
        try:
            _, neighbor_id = message.get("payload").split(":")
            if neighbor_id != self.node_id and int(message.get("rssi")) > self.quality_neighbor:
                if neighbor_id not in self.neighbors:
                    print(message)
                    self.neighbors.add(neighbor_id)
                    print(f"{self.node_id} descubrió al vecino {neighbor_id}")
        except Exception as e:
            print(f"Error procesando HELLO: {e}")
    
    def process_rreq(self, message):
        """
        Procesa un mensaje RREQ recibido, manejando tanto rutas vacías como no vacías.
        """
        try:
            print(message)
            sequence, source, destination, rreq_id, routelist = self.extract_message_data(message)
            if not routelist:
                self.process_empty_routelist(sequence, source, destination, rreq_id)
            else:
                self.process_non_empty_routelist(sequence, source, destination, rreq_id, routelist)
        except Exception as e:
            print(f"Error procesando RREQ: {e}")

    def extract_message_data(self, message):
        """
        Extrae los campos de un mensaje RREQ.
        """
        sequence, source, destination, rreq_id, route = message.get('payload').split(":")
        routelist = route.split("-") if route else []
        return sequence, source, destination, rreq_id, routelist

    def process_empty_routelist(self, sequence, source, destination, rreq_id):
        """
        Procesa un RREQ con lista de ruta vacía.
        """
        if source in self.neighbors:
            if destination == self.node_id:
                print(f"Yo {self.node_id} soy el destino, enviando RREP a {source}")
                self.send_rrep_with_routelist(source, rreq_id, [])
            else:
                self.relay_rreq_if_needed(sequence, source, destination, rreq_id, [])

    def process_non_empty_routelist(self, sequence, source, destination, rreq_id, routelist):
        """
        Procesa un RREQ con lista de ruta no vacía.
        """
        if routelist[-1] in self.neighbors:
            if destination == self.node_id:
                print(f"Yo {self.node_id} soy el destino, enviando RREP a {source}")
                self.send_rrep_with_routelist(source, rreq_id, routelist)
            else:
                self.relay_rreq_if_needed(sequence, source, destination, rreq_id, routelist)
        else:
            pass

    def send_rrep_with_routelist(self, source, rreq_id, routelist):
        """
        Envía un RREP usando la lista de ruta proporcionada.
        """
        routelist.reverse()
        self.query["RREQ"].append([rreq_id, source, self.node_id])
        self.send_rrep(source, rreq_id, routelist)

    def relay_rreq_if_needed(self, sequence, source, destination, rreq_id, routelist):
        """
        Reenvía un RREQ si no ha sido procesado antes.
        """
        if not [rreq_id, source, destination] in self.query["RREQ"]:
            routelist.append(self.node_id)
            finalmessage = f"{sequence}:{source}:{destination}:{rreq_id}:{'-'.join(routelist)}"
            self.query["RREQ"].append([rreq_id, source, destination])
            self.lora.send(finalmessage)
    
    def process_rrep(self, message):
        """
        Procesa un mensaje RREP recibido, actualizando rutas y reenviando si es necesario.
        """
        try:
            print(message)
            _, source, destination, rrep_id, route = message.split(":")
            routelist = route[0].split("-") if route else []

            if destination == self.node_id:
                if not [rrep_id, source, destination] in self.query["RREP"]:
                    self.query["RREP"].append([rrep_id, source, destination])
                    routelist.reverse()
                    print(f"Mensaje recibido de la petición {rrep_id}. La ruta hacia {source} es {routelist}")
                    self.routes[source] = routelist

            else:
                # Nodo intermedio, reenviar RREP si no fue procesado ya
                if self.node_id in routelist:
                    if not [rrep_id, source, destination] in self.query["RREP"]:
                        print(f"Nodo de camino inverso: {self.node_id} reenvía RREP: {message}")
                        self.query["RREP"].append([rrep_id, source, destination])
                        self.lora.send(message)
                    else:
                        print("Mensaje ya reenviado")
                else:
                    pass
        except Exception as e:
            print(f"Error procesando RREP: {e}")
    
    def process_data(self, message):
        """
        Procesa un mensaje DATA recibido, respondiendo si es el destino o reenviando si es nodo intermedio.
        """
        try:
            print(message)
            _, source, destination, data_id, *routelist = message.get('payload').split(':')
            if destination == self.node_id:
                if not [data_id, source, destination] in self.query["DATA"]:
                    self.query["DATA"].append([data_id, source, destination])
                    ruta = routelist[0].split("-")
                    ruta.reverse()
                    de_ruta = '-'.join(ruta)
                    self.routes[source] = ruta
                    self.send_response(source, data_id, de_ruta)

            else:
                if self.node_id in routelist:
                    if not [data_id, source, destination] in self.query["DATA"]:
                        print(f"Nodo de transicion: {self.node_id} reenvía DATA: {message.get('payload')}")
                        self.query["DATA"].append([data_id, source, destination])
                        self.lora.send(message.get('payload'))
                    else:
                        print("Mensaje ya reenviado")
                else:
                    pass
        except Exception as e:
            print(f"Error procesando DATA: {e}")

    def process_response(self, message):
        """
        Procesa un mensaje RESP recibido, reenviando si es nodo intermedio o mostrando los datos si es el destino.
        """
        try:
            _, source, destination, data_id, routelist, sensors, checksum = message.get('payload').split(":")
            routelist = routelist.split("-")
            if not destination == self.node_id:
                if self.node_id in routelist:
                    if not [data_id, source, destination] in self.query["RESP"]:
                        self.query["RESP"].append([data_id, source, destination])
                        self.lora.send(message.get('payload'))
                        print(f"Nodo de transicion: {self.node_id} reenvía RESP: {message.get('payload')}")
            elif destination == self.node_id:
                if self.verify_checksum(message.get('payload')):
                    sequence, source, destination, data_id, routelist, sensors_data, checksum = message.get('payload').split(":")
                    if destination == self.node_id and data_id == self.query["DATA"][-1][0]:
                        if not [data_id, source, destination] in self.query["RESP"]:
                            self.query["RESP"].append([data_id, source, destination])
                            print(f"{self.node_id} recibió respuesta de la petición {data_id} con los datos {sensors_data}")
                            self.waiting_response = False
                else:
                    print(f"{self.node_id} no recibió un checksum correcto")
        except Exception as e:
            print(f"Error procesando RESP: {e}")

# Sugerencias de mejora:
# - Agregar logs opcionales para depuración.
# - Permitir configuración dinámica de parámetros como MAX_ATTEMPTS y TIMEOUT.