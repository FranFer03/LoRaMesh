class DSRNode:
    def __init__(self, node_id, lora, qos = -80,timestamp=20):
        self.node_id = node_id
        self.neighbors = set()  # Vecinos directos
        self.quality_neighbor = qos
        self.routing_table = {}  # Tabla de rutas: destino -> lista de saltos
        self.rreq_id = 0  # ID único para cada RREQ
        self.pending_rreqs = {}  # Solicitudes RREQ pendientes (ID -> destino)
        self.lora = lora  # Instancia de la clase LoRa
        self.timestamp_message = timestamp

    def set_timestamp(self,seconds):
        self.timestamp_message = seconds

    def send_hello(self):
        """Envía un mensaje de hello para descubrir vecinos"""
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)
    
    def broadcast_rreq(self, destination):
        """Envía un mensaje RREQ a la red para descubrir rutas"""
        self.rreq_id = self.timestamp_message
        rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}"
        print(f"{self.node_id} enviando RREQ: {rreq_message}")
        # Envía en broadcast a todos los vecinos usando LoRa
        self.lora.send(rreq_message)
        # Almacena la solicitud pendiente
        self.pending_rreqs[self.rreq_id] = destination

    def send_rrep(self, source, message):
        """Envía un RREP al nodo origen por la ruta inversa"""
        print(f"{self.node_id} enviando RREP a {source}: {message}")
        self.lora.send(message)

    """def send_data(self, data, destination):
        ""Envía datos utilizando una ruta completa ya descubierta""
        route = self.routing_table.get(destination)
        if route:
            print(f"{self.node_id} enviando datos a {destination} vía {route}")
            
            # El mensaje contiene la ruta completa
            data_message = f"DATA:{self.node_id}:{destination}:{data}:{':'.join(route)}"
            
            # Enviar el mensaje con la ruta completa
            self.lora.send(data_message)
        else:
            print(f"Ruta a {destination} no encontrada, enviando RREQ...")
            self.broadcast_rreq(destination)
    """
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
            """
            elif message.startswith("DATA"):
                self.forward_data(message)
            
            else:
                print("Mensaje sin reconocer")
            """
    
    def process_hello(self, message):
        """Procesa un mensaje HELLO recibido y agrega al nodo a la lista de vecinos"""
        try:
            _, neighbor_id = message.get("payload").split(":")
            if neighbor_id != self.node_id and int(message.get("rssi")) > self.quality_neighbor:
                if not neighbor_id in self.neighbors:
                    self.neighbors.add(neighbor_id)
                    print(f"{self.node_id} descubrió al vecino {neighbor_id}")
                else:
                    pass
        except:
            pass
            # Evita agregar a sí mismo
            

    
    def process_rreq(self, message):
        """Procesa un mensaje RREQ recibido"""
        try:
            _, source, destination, rreq_id = message.split(":")
            if destination == self.node_id:
                # Este nodo es el destino, enviar RREP
                print(f"{self.node_id} es el destino, enviando RREP a {source}")
                rrep_message = f"RREP:{self.node_id}:{source}:{rreq_id}"
                self.send_rrep(source, rrep_message)
            else:
                # Nodo intermedio, reenviar RREQ
                print(f"{self.node_id} reenvía RREQ: {message}")
                self.lora.send(message)
        except:
            pass
    
    def process_rrep(self, message):
        try:
            """Procesa un mensaje RREP recibido"""
            _, destination, source, rrep_id, *route = message.split(":")
            
            # Agregar este nodo a la ruta
            route.append(self.node_id)
            
            if destination == self.node_id:
                # Este nodo es el origen, almacena la ruta completa en la tabla de rutas
                complete_route = route[::-1]  # La revertimos para que sea origen -> destino
                print(f"{self.node_id} almacena la ruta hacia {source}: {complete_route}")
                self.routing_table[source] = complete_route
            
            else:
                # Nodo intermedio, reenviar RREP agregando este nodo a la ruta
                #new_message = f"RREP:{destination}:{source}:{rrep_id}:{':'.join(route)}"
                #print(f"{self.node_id} reenvía RREP: {new_message}")
                #self.lora.send(new_message)
                pass
        except:
            pass

    """
    def forward_data(self, message):
        ""Reenvía el mensaje de datos hacia el destino utilizando la ruta completa""
        _, source, destination, data, *route = message.split(":")
        
        if destination == self.node_id:
            print(f"{self.node_id} recibió datos: {data}")
        else:
            # Extraer el siguiente salto de la ruta
            if route:
                next_hop = route[0]
                # Remover el nodo actual de la ruta y reenviar el mensaje
                new_route = route[1:]
                
                # Formar el nuevo mensaje con la ruta actualizada
                new_message = f"DATA:{source}:{destination}:{data}:{':'.join(new_route)}"
                
                print(f"{self.node_id} reenvía datos a {destination} vía {next_hop}")
                self.lora.send(new_message)
            else:
                print(f"Error: No se puede reenviar, la ruta está vacía")
    """