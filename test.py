def remove_query(command, element):
    query = {'RREP': [], 'RREQ': [['784317687', 'A', 'B'],['784317689', 'A', 'B']], 'DATA': [], 'RESP': []}
    try:
        # Filtrar las sublistas que contienen el elemento y eliminarlas
        initial_len = len(query[command])
        query[command] = [sublist for sublist in query[command] if element not in sublist]
        
        # Verificar si se eliminó alguna sublista
        if len(query[command]) < initial_len:
            print(f"La orden con el '{element}' ha sido exitosamente eliminada del comando '{command}'.")
        else:
            print(f"No se encuentra el query con el elemento '{element}'.")
        
        print(query)
    except KeyError:
        print(f"No existe el comando '{command}' en el diccionario.")

remove_query("RREQ", '784317689')
