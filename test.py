query = {
    "DATA": [["10", "A", "B"], ["11", "C", "H"]]  # Convertimos en una lista de listas
}

data_id = "10"
source = "A"
destination = "B"

print([data_id, source, destination] in query["DATA"])


