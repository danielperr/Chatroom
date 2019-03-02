import socket as s 
import threading, thread, re, time, scapy.all
from datetime import datetime

BUFFER_SIZE = 1024
HOST = 'localhost'
USERNAME_WHITELIST = r'^[a-zA-Z\._-]*$'
PASSWORD = 'sumsum_hipatah'


port = 0

users = {
    # address: (client_socket, username)
}

is_shutting_down = False # used for closing all threads

def find_free_port():
    '''
    Finds a free port for the server to use
    and returns it (int)
    '''
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    sock.bind(('', 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    sock.close()
    return port

def wait_for_port_request():
    while True:
        if is_shutting_down:
            break

        requests = scapy.all.sniff(
            filter = 'icmp',
            count = 1,
            lfilter = lambda p: 'chat-request-port' in str(p), # searching for raw data in packet
            timeout = 1
        )

        if len(requests) == 0:
            continue
        
        packet = requests[0]
        scapy.all.send(
            scapy.all.IP(
                dst = packet['IP'].src,
                src = packet['IP'].dst
            ) / scapy.all.ICMP() / ('chat-reply-' + str(port))
        )

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

def close_all_client_sockets():
    '''
    Closes all client sockets in 'users' dictionary
    '''
    for addr in users.keys():
        users[addr][0].close()

def handle_connection(server_socket, client_socket, address):
    global sockets, users, is_shutting_down

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

        if is_shutting_down:
            break

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
                    msg = '[*] %s sent you : %s' % (username, ' '.join(data.split()[2:]))
                    send_to_username(data.split()[1], msg)
                except ValueError, e:
                    client_socket.send('[x] ERROR: ' + str(e))
                except IndexError:
                    client_socket.send('[x] ERROR: please specify username and the message.')
                else:
                    client_socket.send('[*] You sent %s : %s' % (data.split()[1], ' '.join(data.split()[2:])))
            
            elif data.startswith('/shutdown'):
                if len(data.split()) == 1:
                    client_socket.send('[x] ERROR: please provide a password too')
                
                elif ' '.join(data.split()[1:]) == PASSWORD:
                    client_socket.send('[*] Shutting down . . .')
                    time.sleep(0.01)
                    broadcast('/off')
                    server_socket.close()
                    is_shutting_down = True

                    # Opening a temporary socket to free the .accept method in main()
                    closing_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
                    closing_socket.connect((HOST, port))
                    closing_socket.close()
                    break
                
                else:
                    client_socket.send('[x] Wrong password')
            
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
    global port

    port = find_free_port()
    server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    server_socket.bind((HOST, port))
    server_socket.listen(2)
    print '[*] Listening on port %s . . .' % port

    thread.start_new_thread(wait_for_port_request, ())

    while True:
        client_socket, address = server_socket.accept()
        
        if is_shutting_down:
            break
        
        thread.start_new_thread(handle_connection, (server_socket, client_socket, address))
    
    quit()

if __name__ == '__main__':
    main()