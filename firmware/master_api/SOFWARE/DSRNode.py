import time
from machine import Timer # type: ignore
import random

class DSRNode:
    """
    Implementa un nodo para una red mesh basada en el protocolo DSR (Dynamic Source Routing)
    usando LoRa como medio de comunicación.
    """
    MAX_ATTEMPTS = 2
    RETRY_INTERVAL = 30
    TIMEOUT = 62
    CACHE_TIMEOUT = 180

    def __init__(self, node_id, lora, rtc, timer, qos=-80, role="slave"):
        """
        Inicializa el nodo DSR con los parámetros necesarios.
        """
        self.neighbors = set()
        self.rreq_id = 0
        self.query = {
            "RREQ": [],
            "RREP": [],
            "DATA": [],
            "RESP": []
        }
        self.routes = {}
        self.node_id = node_id
        self.quality_neighbor = qos
        self.lora = lora
        self.timestamp_message = 0
        self.rtc = rtc
        self.timer = timer
        self.role = role
        self.waiting_response = False
        self.response_timer = 0
        self.attempts = 0
        self.sent_message = None

        # Inicializa el temporizador para actualizar el timestamp y limpiar la caché periódicamente
        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.set_timestamp)

        print(f"Node {self.node_id} is operating as {self.role}.")

    def set_timestamp(self, timer):
        """
        Actualiza el timestamp del nodo usando el RTC y limpia la caché de mensajes antiguos.
        """
        rtc_time = self.rtc.datetime()
        t = (rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[4], rtc_time[5], rtc_time[6], 0, 0, 0)
        self.timestamp_message = time.mktime(t)
        self.cache_cleaning()

    def remove_query(self, command, element):
        """
        Elimina un elemento de la lista de consultas (query) para un comando específico.
        """
        try:
            initial_len = len(self.query[command])
            self.query[command] = [sublist for sublist in self.query[command] if element not in sublist]
            if len(self.query[command]) < initial_len:
                print(f"La orden con el '{element}' ha sido eliminada del comando '{command}'.")
            else:
                print(f"No se encuentra el elemento '{element}' en el comando '{command}'.")
        except KeyError:
            print(f"No existe el comando '{command}' en el diccionario.")
    
    def cache_cleaning(self):
        """
        Elimina mensajes antiguos de la caché según el tiempo de expiración definido.
        """
        for cmd in ["RREQ", "RREP", "DATA", "RESP"]:
            self.query[cmd] = [i for i in self.query[cmd] if self.timestamp_message - int(i[0]) < self.CACHE_TIMEOUT]

    def calculate_checksum(self, message):
        """
        Calcula un checksum simple para verificar la integridad de los mensajes.
        """
        message_bytes = message.encode('utf-8')
        checksum = 0
        for i in range(0, len(message_bytes), 2):
            word = message_bytes[i]
            if i + 1 < len(message_bytes):
                word = (word << 8) + message_bytes[i + 1]
            checksum += word
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        return ~checksum & 0xFFFF

    def verify_checksum(self, message_with_checksum):
        """
        Verifica que el checksum de un mensaje recibido sea correcto.
        """
        *message_parts, received_checksum = message_with_checksum.rsplit(":", 1)
        message = ":".join(message_parts)
        return int(received_checksum) == self.calculate_checksum(message)

    def send_hello(self):
        """
        Envía un mensaje HELLO para anunciar la presencia del nodo a sus vecinos.
        """
        hello_message = f"HELLO:{self.node_id}"
        self.lora.send(hello_message)
    
    def send_response(self, destination, id_response, routelist):
        """
        Envía una respuesta RESP con datos simulados de sensores.
        """
        temp = random.uniform(50, 100)
        humidity = random.uniform(0, 100)
        data_message_raw = f"RESP:{self.node_id}:{destination}:{id_response}:{routelist}:{temp},{humidity}"
        checksum = self.calculate_checksum(data_message_raw)
        data_message = f"{data_message_raw}:{checksum}"
        self.lora.send(data_message)

    def broadcast_rreq(self, destination):
        """
        Difunde un mensaje RREQ para descubrir rutas hacia un destino.
        """
        self.rreq_id = self.timestamp_message
        rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}:"
        self.query["RREQ"].append([str(self.rreq_id), self.node_id, destination])
        self.lora.send(rreq_message)

    def send_rrep(self, destination, id_message, routes):
        """
        Envía un mensaje RREP con la ruta descubierta hacia el destino.
        """
        rrep_message = f"RREP:{self.node_id}:{destination}:{id_message}:{'-'.join(routes)}"
        self.query["RREP"].append([id_message, self.node_id, destination])
        self.lora.send(rrep_message)
    
    def request_data(self, destination):
        """
        Solicita datos a un nodo destino usando la ruta conocida.
        Si no hay ruta, inicia el descubrimiento de ruta.
        """
        if destination in self.routes.keys():
            print(f"{self.node_id} enviando solicitud de datos a {destination} a través de la ruta {self.routes[destination]}")
            data_message = f"DATA:{self.node_id}:{destination}:{self.timestamp_message}:{'-'.join(self.routes[destination])}"
            self.query["DATA"].append([str(self.timestamp_message), self.node_id, destination])
            self.lora.send(data_message)
            self.waiting_response = True
            self.response_timer = time.time()
            self.attempts = 1
            self.sent_message = data_message
        else:
            print(f"{self.node_id} no se puede enviar DATA a {destination} porque no hay ruta disponible.")
            self.broadcast_rreq(destination)

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