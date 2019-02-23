import socket as s

BUFFER_SIZE = 1024

HOST = 'localhost'
PORT = 30000
ADDRESS = (HOST, PORT)


def main():
    print '[*] Trying to connect to %s:%s . . .' % ADDRESS
    client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    client_socket.connect(ADDRESS)
    print '[v] Connection successful !'

    while True:
        data = raw_input('> ')
        if not data: break
        client_socket.send(data)
        data = client_socket.recv(BUFFER_SIZE)
        if not data: break
        print data

    print '[x] Disconnected'
    client_socket.close()

if __name__ == '__main__':
    main()