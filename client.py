import socket as s
import threading, thread

BUFFER_SIZE = 1024

HOST = 'localhost'
PORT = 30000
ADDRESS = (HOST, PORT)

USERNAME = 'hellu'

def recieve(client_socket):
    while True:
        data = client_socket.recv(BUFFER_SIZE)
        if not data: break
        print data

def input_send(client_socket):
    while True:
        data = raw_input('> ')
        if not data: break
        client_socket.send(data)
    
    print '[x] Disconnected'
    client_socket.close()
    exit()

def main():

    print '[*] Trying to connect to %s : %s . . .' % ADDRESS

    client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    client_socket.connect(ADDRESS)

    client_socket.send(USERNAME)
    response = client_socket.recv(BUFFER_SIZE)
    if response == 'ok':
        print '[v] Logged in as :', USERNAME
    else:
        print '[x] Username already exists!'
        return
    
    print '[v] Connection successful!'

    thread.start_new_thread(recieve, (client_socket, ))
    thread.start_new_thread(input_send, (client_socket, ))

if __name__ == '__main__':
    main()