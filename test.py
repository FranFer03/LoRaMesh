timestamp_message = 150
CACHE_TIMEOUT = 60

query = {
    "RREQ": [["10", "A", "B"], ["130", "A", "J"]]  # Convertimos en una lista de listas
}

# Iteramos sobre una copia de la lista para evitar problemas de modificación durante el recorrido
for z, i in enumerate(query["RREQ"][:]):
    if timestamp_message - int(i[0]) >= CACHE_TIMEOUT:
        query["RREQ"].remove(i)
