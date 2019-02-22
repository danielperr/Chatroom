import socket as s 
import threading
import thread

BUFFER_SIZE = 1024

HOST = 'localhost'
PORT = 30000
ADDRESS = (HOST, PORT)


# ---------- NETWORK ----------

def handle_connection(client_socket, address):
    print '[v] Started communication with :', address

    while True:
        data = client_socket.recv(BUFFER_SIZE)
        if not data: break
        msg = 'echoed:... ' + data
        client_socket.send(msg)
    
    print '[x] Ended communication with :' , address
    client_socket.close()


def main():
    server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    server_socket.bind(ADDRESS)
    server_socket.listen(2)
    print '[*] Listening on port %s . . .' % PORT

    while True:
        client_socket, address = server_socket.accept()
        thread.start_new_thread(handle_connection, (client_socket, address))

if __name__ == '__main__':
    print help()