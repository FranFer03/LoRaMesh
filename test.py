query = {
    "RREQ": [["10", "A", "B"], ["130", "A", "J"]]  # Convertimos en una lista de listas
}

def remove_query(query_dict, command, element):
    try:
        # Filtramos sublistas que contengan el elemento y las eliminamos
        initial_len = len(query_dict[command])
        query_dict[command] = [sublist for sublist in query_dict[command] if element not in sublist]
        
        # Verificar si se eliminó alguna sublista
        if len(query_dict[command]) < initial_len:
            print(f"Elemento '{element}' eliminado exitosamente del comando '{command}'.")
        else:
            print(f"No se encuentra el query con el elemento '{element}'.")
            
    except KeyError:
        print(f"No existe el comando '{command}' en el diccionario.")

remove_query(query, "RREQ", "20")

print(query)
