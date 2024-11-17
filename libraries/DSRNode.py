import time
from machine import Timer
import random

class DSRNode:
    MAX_ATTEMPTS = 2
    RETRY_INTERVAL = 30
    TIMEOUT = 62
    CACHE_TIMEOUT = 180

    def __init__(self, node_id, lora, rtc, timer, qos=-80, role="slave"):
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


        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.set_timestamp)

        print(f"Node {self.node_id} is operating as {self.role}.")


    def set_timestamp(self, timer):
        rtc_time = self.rtc.datetime()
        t = (rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[4], rtc_time[5], rtc_time[6], 0, 0, 0)
        self.timestamp_message = time.mktime(t)
        self.cache_cleaning()

    def remove_query(self, command, element):
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
        for cmd in ["RREQ", "RREP","DATA","RESP"]:
            self.query[cmd] = [i for i in self.query[cmd] if self.timestamp_message - int(i[0]) < self.CACHE_TIMEOUT]

    def calculate_checksum(self, message):
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
        *message_parts, received_checksum = message_with_checksum.rsplit(":", 1)
        message = ":".join(message_parts)
        return int(received_checksum) == self.calculate_checksum(message)

    def send_hello(self):
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)
    
    def send_response(self,destination,id_response, routelist):
        temp = random.uniform(50,100)
        humidity = random.uniform(0,100)
        data_message_raw = f"RESP:{self.node_id}:{destination}:{id_response}:{routelist}:{temp},{humidity}"
        checksum = self.calculate_checksum(data_message_raw)
        data_message = f"{data_message_raw}:{checksum}"
        self.lora.send(data_message)

    def broadcast_rreq(self, destination):
        self.rreq_id = self.timestamp_message
        rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}:"
        self.query["RREQ"].append([str(self.rreq_id),self.node_id,destination])
        self.lora.send(rreq_message)

    def send_rrep(self, destination,id_message,routes):
        print(f"{self.node_id} envia RREP a {destination}: {id_message}: {'-'.join(routes)}")
        rrep_message = f"RREP:{self.node_id}:{destination}:{id_message}:{'-'.join(routes)}"
        self.query["RREP"].append([id_message, self.node_id, destination])
        self.lora.send(rrep_message)
    
    def request_data(self, destination):
        if destination in self.routes.keys():
            print(f"{self.node_id} enviando solicitud de datos a {destination} a través de la ruta {self.routes[destination]}")
            data_message = f"DATA:{self.node_id}:{destination}:{self.timestamp_message}:{'-'.join(self.routes[destination])}"
            self.query["DATA"].append([str(self.timestamp_message), self.node_id, destination])
            self.lora.send(data_message)
            self.waiting_response = True
            # Almacenar detalles para el temporizador
            self.response_timer = time.time()
            self.attempts = 1
            self.sent_message = data_message
        else:
            print(f"{self.node_id} no se puede enviar DATA a {destination} porque no hay ruta disponible.")
            self.broadcast_rreq(destination)

    def waiting_for_response(self):
        if self.waiting_response:
            current_time = time.time()
            time_elapsed = current_time - self.response_timer
            
            if time_elapsed >= self.RETRY_INTERVAL and self.attempts < self.MAX_ATTEMPTS:
                # Reenvío del mensaje después de 15 segundos
                self.response_timer = current_time
                _, resource, redestination, redata_id, reroutelist = self.sent_message.split(":")
                self.query["DATA"][0][0] = self.timestamp_message
                data_message = f"DATA:{resource}:{redestination}:{self.timestamp_message}:{'-'.join(self.routes[redestination])}"
                print(data_message)
                self.lora.send(data_message)
                self.attempts += 1
                print(f"{self.node_id} reenviando mensaje de solicitud de datos {self.query['DATA'][0][0]}")
            
            # Verificar si se ha recibido un paquete
            if self.lora.is_packet_received():
                message = self.lora.get_packet(rssi=True)
                print(f"{self.node_id} recibió mensaje: {message}")
                if message.get('payload').startswith("RESP"):
                    if self.verify_checksum(message.get('payload')):
                        sequence, source, destination, data_id, routelist, sensors_data, checksum = message.get('payload').split(":")
                        if destination == self.node_id and data_id == self.query["DATA"][-1][0]:
                            print(f"{self.node_id} recibió respuesta de la petición {data_id} con los datos {sensors_data}")
                            self.waiting_response = False
                    else:
                        print(f"{self.node_id} no recibió un checksum correcto")
            
            elif time_elapsed > self.TIMEOUT:
                print(f"{self.node_id} no recibió respuesta para la petición {self.query['DATA'][0][0]} por lo tanto la ruta está caída")
                print(self.routes)
                self.waiting_response = False
                try:
                    self.routes.pop(self.query["DATA"][0][2])
                except:
                    pass
    def receive_message(self):
        """Escucha la red y procesa los mensajes recibidos según el tipo de mensaje (HELLO, RREQ, RREP, DATA)."""
        try:
            if self.lora.is_packet_received():
                message = self.lora.get_packet(rssi=True)
                print(f"{self.node_id} recibió mensaje: {message}")
                # Procesar diferentes tipos de mensajes
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
        """Procesa un mensaje HELLO recibido y agrega al nodo a la lista de vecinos"""
        try:
            _, neighbor_id = message.get("payload").split(":")
            if neighbor_id != self.node_id and int(message.get("rssi")) > self.quality_neighbor:
                if neighbor_id not in self.neighbors:
                    self.neighbors.add(neighbor_id)
                    print(f"{self.node_id} descubrió al vecino {neighbor_id}")
        except Exception as e:
            print(f"Error procesando HELLO: {e}")
    
    def process_rreq(self, message):
        try:
            sequence, source, destination, rreq_id, routelist = self.extract_message_data(message)
            if not routelist:
                print("Estoy vacia")
                self.process_empty_routelist(sequence, source, destination, rreq_id)
            else:
                print("Tengo algo")
                self.process_non_empty_routelist(sequence, source, destination, rreq_id, routelist)
        
        except Exception as e:
            print(f"Error procesando RREQ: {e}")

    def extract_message_data(self, message):
        sequence, source, destination, rreq_id, route = message.get('payload').split(":")
        routelist = route.split("-") if route else []
        return sequence, source, destination, rreq_id, routelist

    def process_empty_routelist(self, sequence, source, destination, rreq_id):
        if source in self.neighbors:
            if destination == self.node_id:
                print(f"Ahh...soy yo wey {self.node_id} es el destino, enviando RREP a {source}")
                self.send_rrep_with_routelist(source, rreq_id, [])
            else:
                self.relay_rreq_if_needed(sequence, source, destination, rreq_id, [])

    def process_non_empty_routelist(self, sequence, source, destination, rreq_id, routelist):
        if routelist[-1] in self.neighbors:
            if destination == self.node_id:
                print(f"Ahh...soy yo wey {self.node_id} es el destino, enviando RREP a {source}")
                self.send_rrep_with_routelist(source, rreq_id, routelist)
            else:
                self.relay_rreq_if_needed(sequence, source, destination, rreq_id, routelist)
        else:
            print(f"El mensaje RREQ no fue recibido por un vecino")

    def send_rrep_with_routelist(self, source, rreq_id, routelist):
        routelist.reverse()
        self.query["RREQ"].append([rreq_id, source, self.node_id])
        self.send_rrep(source, rreq_id, routelist)

    def relay_rreq_if_needed(self, sequence, source, destination, rreq_id, routelist):
        if not [rreq_id, source, destination] in self.query["RREQ"]:
            routelist.append(self.node_id)
            finalmessage = f"{sequence}:{source}:{destination}:{rreq_id}:{'-'.join(routelist)}"
            print(f"Nodo intermedio: {self.node_id} reenvía RREQ: {finalmessage}")
            self.query["RREQ"].append([rreq_id, source, destination])
            self.lora.send(finalmessage)
    
    def process_rrep(self, message):
        try:
            sequence, source, destination, rrep_id, route = message.split(":")
            routelist = route[0].split("-") if route else []

            if destination == self.node_id:
                routelist.reverse()
                print(f"Volvistee wey. La ruta hacia {source} es {routelist}")
                self.routes[source] = routelist
                self.remove_query("RREQ",rrep_id)

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
        """Procesa un mensaje DATA recibido """
        try:
            sequence, source, destination, data_id, routelist = self.extract_message_data(message)

            if destination == self.node_id:
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
            print(f"Error procesando RREP: {e}")

    def process_response(self, message):
        """Procesa un mensaje RESP recibido """
        try:
            
            sequence, source, destination, data_id, routelist, sensors, checksum = message.get('payload').split(":")
            routelist = routelist.split("-")
            if not destination == self.node_id:
                if self.node_id in routelist:
                    if not [data_id, source, destination] in self.query["RESP"]:
                        self.query["RESP"].append([data_id, source, destination])
                        self.lora.send(message.get('payload'))
                        print(f"Nodo de transicion: {self.node_id} reenvía RESP: {message.get('payload')}")
                    else:
                        pass             
                else:
                    pass
            elif destination == self.node_id:
                if self.verify_checksum(message.get('payload')):
                    sequence, source, destination, data_id, routelist, sensors_data, checksum = message.get('payload').split(":")
                    if destination == self.node_id and data_id == self.query["DATA"][-1][0]:
                        print(f"{self.node_id} recibió respuesta de la petición {data_id} con los datos {sensors_data}")
                        self.waiting_response = False
                else:
                    print(f"{self.node_id} no recibió un checksum correcto")
        except Exception as e:
            print(f"Error procesando RESP: {e}")
