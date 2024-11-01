import time

class DSRNode:
    MAX_ATTEMPTS = 4
    RETRY_INTERVAL = 5
    TIMEOUT = 20
    CACHE_TIMEOUT = 60   

    def __init__(self, node_id, lora,timer, qos=-80, timestamp=20):
        self.neighbors = set()
        self.rreq_id = 0
        self.query = {
            "RREQ":[],
            "RREP":[]
        }
        self.routes = {}
        self.node_id = node_id
        self.quality_neighbor = qos
        self.lora = lora 
        self.timestamp_message = timestamp        
        self.start_time = None
        self.timer = timer
        self.time_pending_rreqs = []

        self.timer.init(mode=self.timer.ONE_SHOT, period=1, callback=self.set_times)
    
    @property
    def get_neighbors(self):
        return print(f"Vecinos proximos: {self.neighbors}")
    
    @property
    def get_routes(self):
        return print(f"Rutas disponibles: {self.routes}")

    def cache_cleaning(self):
        for z, i in enumerate(self.query["RREQ"][:]):
            if self.timestamp_message - int(i[0]) >= self.CACHE_TIMEOUT:
                self.query["RREQ"].remove(i)
        for z, i in enumerate(self.query["RREP"][:]):
            if self.timestamp_message - int(i[0]) >= self.CACHE_TIMEOUT:
                self.query["RREP"].remove(i)

    def set_timestamp(self, seconds):
        self.timestamp_message = seconds

    def send_hello(self):
        """Envía un mensaje de hello para descubrir vecinos"""
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)
    
    def send_ack(self,source,id_req):
        ack_message = f"ACK:{self.node_id}:{source}:{id_req}"
        print(f"{self.node_id} envio ACK para {source} por request {id_req}")
        self.lora.send(ack_message)

    def broadcast_rreq(self, destination):
        """Envía un mensaje RREQ a la red para descubrir rutas, con reintentos y control de expiración."""
        self.rreq_id = self.timestamp_message
        rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}:"
        #self.time_pending_rreqs.append(time.time())
        self.query["RREQ"] = [str(self.rreq_id),self.node_id,destination]
        self.lora.send(rreq_message)

    def send_rrep(self, destination,id_message,routes):
        """Envía un RREP al nodo origen por la ruta inversa"""
        print(f"{self.node_id} envia RREP a {destination}: {id_message}: {'-'.join(routes)}")
        rrep_message = f"RREP:{self.node_id}:{destination}:{id_message}:{'-'.join(routes)}"
        self.query["RREP"].append([id_message, self.node_id, destination])
        self.lora.send(rrep_message)

    def receive_message(self):
        """Escucha la red y procesa los mensajes recibidos"""
        if self.lora.is_packet_received():
            message = self.lora.get_packet(rssi=True)
            print(f"{self.node_id} recibió mensaje: {message}")
            if message.get('payload').startswith("HELLO"):
                self.process_hello(message)
            elif message.get('payload').startswith("RREQ"):
                self.process_rreq(message.get('payload'))
            elif message.get('payload').startswith("RREP"):
                self.process_rrep(message.get('payload'))
            elif message.get('payload').startswith("DATA"):
                self.forward_data(message.get('payload'))

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
        """Procesa un mensaje RREQ recibido """
        try:
            sequence, source, destination, rreq_id, *route = message.split(":")
            routelist = route[0].split("-")

            if destination == self.node_id:
                print(f"Ahh...soy yo wey {self.node_id} es el destino, enviando RREP a {source}")
                routelist.reverse()
                self.query["RREQ"].append([rreq_id, source, destination])
                self.send_rrep(source, rreq_id,routelist)
            
            else:
                # Nodo intermedio, reenviar RREQ si no fue procesado ya
                if not [rreq_id, source, destination] in self.query["RREQ"]:
                    routelist.append(self.node_id)
                    finalmessage = f"{sequence}:{source}:{destination}:{rreq_id}:{'-'.join(routelist)}"
                    print(f"Nodo intermedio: {self.node_id} reenvía RREQ: {finalmessage}")
                    self.query["RREQ"].append([rreq_id, source, destination])
                    self.lora.send(finalmessage)
                else:
                    print("Mensaje ya reenviado")
                    
        except Exception as e:
            print(f"Error procesando RREQ: {e}")

    
    def process_rrep(self, message):
        """Procesa un mensaje RREP recibido """
        try:
            sequence, source, destination, rrep_id, *route = message.split(":")
            routelist = route[0].split("-")

            if destination == self.node_id:
                routelist.reverse()
                print(f"Volvistee wey. La ruta hacia {source} es {routelist}")
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
    
    def forward_data(self):
        pass