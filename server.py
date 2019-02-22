import socket as s
import threading, thread

BUFFER_SIZE = 1024

HOST = 'localhost'
PORT = 50008
ADDRESS = (HOST, PORT)

def handle_connection(client_socket, address):
    print '[*] Started communication with :', address

    while True:
        data = client_socket.recv(BUFFER_SIZE)
        if not data: break
        msg = data
        client_socket.send(msg)
    
    client_socket.close()
    print '[*] Ended communication with :', address


def main():

    server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    server_socket.bind(ADDRESS)
    server_socket.listen(2)

    print '[*] Listening on port %s . . .' % PORT

    while True:
        client_socket, address = server_socket.accept()
        thread.start_new_thread(handle_connection, (client_socket, address))