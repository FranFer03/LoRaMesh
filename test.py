message = "DATA:E:A:1000:D-B:temp=40,hum=30:62744"
sequence, source, destination, data_id, routelist, sensors, checksum = message.split(":")
#routelist = routelist.tolist()
routelist = routelist.split("-")
print(routelist)



#    if not destination == node_id:
