import socket as s 
import threading, thread

BUFFER_SIZE = 1024

HOST = 'localhost'
PORT = 30000
ADDRESS = (HOST, PORT)

users = {
    # address: (client_socket, username)
}

def send_to_address(address, msg):
    users[address][0].send(msg)


def broadcast(msg):
    for address in users.keys():
        send_to_address(address, msg)


def handle_connection(client_socket, address):
    global sockets, users

    # Check username
    username = client_socket.recv(BUFFER_SIZE)
    if username in [users[addr][1] for addr in users.keys()]:
        client_socket.close()
        return
    
    # "Handshake"
    users[address] = client_socket, username
    client_socket.send('ok')
    print '<Server> : %s has joined the chat' % username

    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE)
        except: break
        if not data: break
        print '\t[%s] > %s' % (users[address][1], data)
        broadcast(msg)
    
    print '<Server> : %s has left the chat' % username
    del users[address]
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
    main()