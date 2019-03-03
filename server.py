'''
server.py
Chatroom using Tkinter, sockets, and scapy
Author: Daniel Peretz
'''


import socket as s
import threading, thread, re, time, scapy.all, random
from datetime import datetime

BUFFER_SIZE = 1024 # Socket buffer size
HOST = 'localhost' # Socket ip address
USERNAME_WHITELIST = r'^[a-zA-Z0-9\._-]*$' # How the server filters usernames
PASSWORD = 'sumsum_hipatah' # Password for server shutdown
HELP = 'Available commands: /time, /msg, /rolladice, /quote, /logout, /shutdown. More info in README.txt' # Help info

QUOTES = [ # Intelligent quotes to be used by the /quote command
    "If you're too open-minded; your brains will fall out.",
    "If you think nobody cares about you, try missing a couple of payments.",
    "Rice is great when you're hungry and you want 2000 of something.",
    "Life is short. Smile while you still have teeth.",
    "When nothing is going right, go left.",
    "If we're not meant to have midnight snacks, why is there a light in the fridge?",
    "My fake plants died because I did not pretend to water them.",
    "Do Wisozki employees take coffee breaks?",
    "If a book about failures doesn't sell, is it a success?",
    "Always go to other people's funerals, otherwise they won't come to yours."
]


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
    '''
    Waits (sniffs) for port request ICMP message.
    '''
    while True:
        if is_shutting_down:
            break

        requests = scapy.all.sniff(
            filter = 'icmp',
            count = 1,
            lfilter = lambda p: 'chat-request-port' in str(p), # searching for raw data in packet
            timeout = 1 # Using a timeout so it can check for shutdown and not block the thread
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

def broadcast(msg):
    '''
    Sends everyone in the users dictionary a message.
    '''
    for address in users.keys():
        send_to_address(address, msg)

def broadcast_online_users():
    '''
    Sends to everyone an update of the online user count.
    '''
    broadcast('/online ' + ' '.join(users[addr][1] for addr in users.keys()))
    # usernames are seperated with space

def handle_connection(server_socket, client_socket, address):
    '''
    Handles a client_socket connection (as a thread)
    '''
    global sockets, users, is_shutting_down

    # Username validation with the client
    username = client_socket.recv(BUFFER_SIZE)
    if username in [users[addr][1] for addr in users.keys()]:
        client_socket.send('[x] ERROR: username already taken!')
        client_socket.close()
        return
    elif not re.match(USERNAME_WHITELIST, username): # Check whitelist validity
        client_socket.send('[x] ERROR: username not valid - use characters, dot, underscore and dash')
        client_socket.close()
        return
    
    # "Handshake"
    users[address] = client_socket, username
    client_socket.send('ok')

    print '[*] %s has joined the chat' % username
    broadcast('[*] %s has joined the chat' % username)

    # We let the client process the message before sending another one straight away
    time.sleep(0.1)
    broadcast_online_users() # Update online users to everyone


    # Message handling
    while True:

        if is_shutting_down:
            break

        try:
            data = client_socket.recv(BUFFER_SIZE).strip()
        except: break
        if not data: break
        print '[%s] > %s' % (users[address][1], data)

        # Check command if exists - command starts with '/', args are space-seperated
        if data[0] == '/':

            if data.startswith('/time'): # returns server date and time
                client_socket.send('[*] Server time : ' + datetime.now().strftime(r'%d/%m/%Y %H:%M:%S'))

            elif data.startswith('/msg'): # sends a private message to the given username
                try:
                    msg = '[*] [%s] %s sent you : %s' % (datetime.now().strftime("%H:%M:%S"), username, ' '.join(data.split()[2:]))
                    send_to_username(data.split()[1], msg)
                except ValueError, e:
                    client_socket.send('[x] ERROR: ' + str(e))
                except IndexError:
                    client_socket.send('[x] ERROR: please specify username and the message.')
                else:
                    client_socket.send('[*] You sent %s : %s' % (data.split()[1], ' '.join(data.split()[2:])))
            
            elif data.startswith('/rolladice'): # rolls a dice and announces it to everyone
                broadcast('[*] [%s] %s has rolled a dice and it\'s a %s!' % (datetime.now().strftime("%H:%M:%S"), username, random.randint(1, 6)))
            
            elif data.startswith('/quote'): # announces a random quote.
                broadcast('[*] [%s] %s quotes: "%s"' % (datetime.now().strftime("%H:%M:%S"), username, random.choice(QUOTES)))
            
            elif data.startswith('/logout'): # user log out
                client_socket.send('/off')
                break

            elif data.startswith('/shutdown'): # shuts the server down if the password is correct
                if len(data.split()) == 1:
                    client_socket.send('[x] ERROR: please provide a password too')
                
                elif ' '.join(data.split()[1:]) == PASSWORD:
                    client_socket.send('[*] Shutting down . . .')
                    time.sleep(0.01)
                    broadcast('/off')
                    is_shutting_down = True

                    # Opening a temporary socket to free the .accept method in main()
                    # (accept() waits for a new connection and blocks the program from terminating)
                    closing_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
                    closing_socket.connect((HOST, port))
                    closing_socket.close()
                    break
                
                else:
                    client_socket.send('[x] Wrong password')
            
            elif data.startswith('/help'): # Displays help information
                client_socket.send('[*] ' + HELP)

            else:
                client_socket.send('[x] Unknown command. ' + HELP)
            
        else:
            # If not a command, broadcasts the data as a chat message
            broadcast('[%s] [%s] > %s' % (datetime.now().strftime("%H:%M:%S"), users[address][1], data))


    # Outside loop
    print '[*] %s has left the chat' % username
    broadcast('[*] %s has left the chat' % username)
    time.sleep(0.01)
    broadcast_online_users()

    if address in users.keys():
        del users[address]
    
    client_socket.close()

def main():
    '''
    Set up of the server
    '''
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
    
    server_socket.close()
    
    quit()
    # When exiting it will announce that sys.excepthook and sys.stderr are missing
    # however, it is a known issue

if __name__ == '__main__':
    main()