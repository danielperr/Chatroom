import socket as s 
import threading, thread, re, time
from datetime import datetime

BUFFER_SIZE = 1024

HOST = 'localhost'
PORT = 30000
ADDRESS = (HOST, PORT)

USERNAME_WHITELIST = r'^[a-zA-Z\._-]*$'

users = {
    # address: (client_socket, username)
}

def send_to_username(username, msg):
    '''
    Sends a chat message to the given username
    '''
    if not username:
        raise ValueError('you must specify the username')
    if not msg:
        raise ValueError('you must specify the message')
    for addr in users.keys():
        if users[addr][1] == username:
            send_to_address(addr, msg)
            return
    raise ValueError('username does not exist')

def send_to_address(address, msg):
    '''
    Sends a chat message to the given address
    '''
    try:
        users[address][0].send(msg)
    except s.error, e:
        if e[0] == 10054: # connection was forcibly closed
            del users[address]

def broadcast_online_users():
    '''
    Sends to everyone updates of the online user count.
    '''
    broadcast('/online ' + ' '.join(users[addr][1] for addr in users.keys()))
    # usernames are seperated with space

def broadcast(msg):
    for address in users.keys():
        send_to_address(address, msg)


def handle_connection(client_socket, address):
    global sockets, users

    # Username validation with the client
    username = client_socket.recv(BUFFER_SIZE)
    if username in [users[addr][1] for addr in users.keys()]:
        client_socket.send('[x] ERROR: username already taken!')
        client_socket.close()
        return
    elif not re.match(USERNAME_WHITELIST, username):
        client_socket.send('[x] ERROR: username not valid - use characters, dot, underscore and dash')
        client_socket.close()
        return
    
    # "Handshake"
    users[address] = client_socket, username
    client_socket.send('ok')

    print '[*] %s has joined the chat' % username
    broadcast('[*] %s has joined the chat' % username)
    time.sleep(0.01)
    broadcast_online_users()




    # Message handling
    while True:

        try:
            data = client_socket.recv(BUFFER_SIZE).strip()
        except: break
        if not data: break
        print '\t[%s] > %s' % (users[address][1], data)

        # Check command if exists - command starts with '/', args are space-seperated
        if data[0] == '/':

            if data.startswith('/time'):
                client_socket.send('[*] Server time : ', datetime.now())

            elif data.startswith('/msg'):
                try:
                    msg = '[*] %s sent you : %s' % (username, data.split()[2])
                    send_to_username(data.split()[1], msg)
                except ValueError, e:
                    client_socket.send('[x] ERROR: ' + str(e))
                else:
                    client_socket.send('[*] You sent %s : %s' % (data.split()[1], data.split()[2]))

        else:
            broadcast('[%s] > %s' % (users[address][1], data))
    



    print '[*] %s has left the chat' % username
    broadcast('[*] %s has left the chat' % username)
    time.sleep(0.01)
    broadcast_online_users()

    if address in users.keys():
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