message = {'rssi': -37, 'payload': 'DATA:A:B:784854199:'}


_, source, destination, data_id, *routelist = message.get('payload').split(':')

print(routelist)