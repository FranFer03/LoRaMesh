message = "RREQ:A:E:10:A-B-F"
seccuence, source, destination, rreq_id, *route = message.split(":")
routelist = route[0].split("-")

# Agregar "C" a routelist si no está ya en la lista
if "C" not in routelist:
    routelist.append("C")
    print(routelist)

routelist.reverse()

# Crear el mensaje final uniendo los elementos de routelist
finalmessage = f"{seccuence}:{source}:{destination}:{rreq_id}:{'-'.join(routelist)}"
print(finalmessage)