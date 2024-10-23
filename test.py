node_id = 1
rreq_id = 2
destination = 3

rreq_message = f"RREQ:{node_id}:{destination}:{rreq_id}"
_, source, destination, rreq_id = rreq_message.split(":")

print(_,source,destination,rreq_id)