try:
    from Tkinter import *
except ImportError:
    from tkinter import *

import socket as s
import time, threading, thread, re
import scapy.all

# GUI
PADDING = 12
MIN_WIDTH = 500
MIN_HEIGHT = 250

ONLINE_LABEL_DEFAULT = 'Online users: '

# NETWORK
PORT = 30000
BUFFER_SIZE = 1024
TIMEOUT = 1 # timeout for waiting for the port reply (in seconds)

# Using a class instead of millions of global variables
class App:
    '''
    Chatroom application
    '''

    def __init__(self):

        self.root = Tk()

        # Window settings
        self.root.update()
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.title('Chat Room')

        # Using paned window for app layout
        # This paned window seperates the top part from the bottom parts
        self.master_pwin = PanedWindow(self.root, orient=VERTICAL)
        self.master_pwin.pack(expand=1, fill=BOTH)

        self.gui_setup_login()

        # This paned window seperates the right and left parts
        self.bottom_pwin = PanedWindow(self.master_pwin)
        self.master_pwin.add(self.bottom_pwin)

        self.gui_setup_actions()
        self.gui_setup_chat()

        self.gui_bind_events()

        self.display_message('Please enter the host address and your wanted username.')

        self.root.mainloop()

    def gui_setup_login(self):
        '''
        Set up login area (top)
        '''

        self.login_frame = Frame(self.master_pwin, padx=PADDING)
        self.master_pwin.add(self.login_frame)

        # Host (IP) entry
        self.login_host_label = Label(self.login_frame, text='Host: ')
        self.login_host_label.pack(side=LEFT, fill=X)
        self.login_host_entry = Entry(self.login_frame)
        self.login_host_entry.pack(side=LEFT, expand=1, fill=X)

        # Username entry
        self.login_username_label = Label(self.login_frame, text='Username: ')
        self.login_username_label.pack(side=LEFT, fill=X)
        self.login_username_entry = Entry(self.login_frame)
        self.login_username_entry.pack(side=LEFT, expand=1, fill=X)

        # Connect button
        self.login_submit_button = Button(self.login_frame, text='Connect')
        self.login_submit_button.pack(side=LEFT, fill=X)

        self.locked_login = False

    def gui_setup_actions(self):
        '''
        Set up actions area (including online users list)
        '''

        self.side_frame = Frame(self.bottom_pwin, padx=PADDING, pady=PADDING)
        self.bottom_pwin.add(self.side_frame)

        self.online_stringvar = StringVar(self.side_frame, value=(ONLINE_LABEL_DEFAULT + '0'))
        self.online_label = Label(self.side_frame, textvariable=self.online_stringvar)
        self.online_label.pack()

        self.online_list = Listbox(self.side_frame)
        self.online_list.pack()

    def gui_setup_chat(self):
        '''
        Set up chat area
        '''

        self.chat_frame = Frame(self.bottom_pwin, padx=PADDING, pady=PADDING)
        self.bottom_pwin.add(self.chat_frame)

        self.msgs_frame = Frame(self.chat_frame)
        self.msgs_frame.pack(side=TOP, expand=1, fill=BOTH)

        self.scrollbar = Scrollbar(self.msgs_frame)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.chat_list = Listbox(self.msgs_frame)
        self.chat_list.pack(side=LEFT, expand=1, fill=BOTH)
        self.chat_list.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.chat_list.yview)

        self.submit_frame = Frame(self.chat_frame)
        self.submit_frame.pack(side=BOTTOM, fill=X)

        self.submit_entry = Entry(self.submit_frame)
        self.submit_entry.pack(side=LEFT, expand=1, fill=X)

        self.submit_button = Button(self.submit_frame, text='Send')
        self.submit_button.pack(side=RIGHT)

        self.lock_chat()

    def gui_bind_events(self):
        '''
        Binds each event to its callback function
        '''

        # Login submit events
        self.login_submit_button.bind('<ButtonRelease-1>', self.login)
        self.login_host_entry.bind('<Return>', self.login)
        self.login_username_entry.bind('<Return>', self.login)

        # Chat submit events
        self.submit_button.bind('<ButtonRelease-1>', self.chat_sendmsg)
        self.submit_entry.bind('<Return>', self.chat_sendmsg)

    def lock_login(self):
        '''
        Locks (disables) the login entries, as well as the button.
        '''
        self.login_submit_button['state'] = DISABLED
        self.login_host_entry['state'] = DISABLED
        self.login_username_entry['state'] = DISABLED
        self.locked_login = True

    def unlock_login(self):
        '''
        Unlocks (enables) the login entries, as well as the button.
        '''
        self.login_submit_button['state'] = NORMAL
        self.login_host_entry['state'] = NORMAL
        self.login_username_entry['state'] = NORMAL
        self.locked_login = False

    def lock_chat(self):
        '''
        Locks (disables) the chat area.
        '''
        self.submit_entry['state'] = DISABLED
        self.submit_button['state'] = DISABLED
        self.locked_chat = True

    def unlock_chat(self):
        '''
        Unlocks (enables) the chat area.
        '''
        self.submit_entry['state'] = NORMAL
        self.submit_button['state'] = NORMAL
        self.locked_chat = False

    def update_online_users(self, usernames):
        '''
        Updates the usernames in the 'online users' list.
        '''
        self.online_list.delete(0, END)

        for username in usernames:
            self.online_list.insert(self.online_list.size()+1, username)
        
        self.online_stringvar.set(ONLINE_LABEL_DEFAULT + str(len(usernames)))

    def display_message(self, msg):
        '''
        Displays the given message on the chat ListBox
        '''

        # Check whether the scrollbar position is overridden. (not at the bottom)
        # If no, it will scroll automatically to the bottom to see the chat
        # If yes, it will not scroll automatically (to not annoy the user)
        autoscroll = self.scrollbar.get()[1] >= 0.95

        self.chat_list.insert(self.chat_list.size()+1, msg)

        col = 'black'
        if msg.startswith('[*]'):
            col = 'blue4'
        elif msg.startswith('[x]'):
            col = 'red4'
        elif msg.startswith('[v]'):
            col = 'green4'
        self.chat_list.itemconfig(self.chat_list.size()-1, {'fg': col})

        # Scroll to the bottom if already at bottom
        if autoscroll:
            self.chat_list.yview_moveto(1.0)

    def login(self, event):
        '''
        Performs login actions, including requesting port,
        verifying the username and connecting via sockets
        '''

        if self.locked_login:
            return
        
        # Getting data from the entries
        host = self.login_host_entry.get()
        username = self.login_username_entry.get()
        
        # Validating input
        if username == '':
            self.display_message('[x] ERROR: please fill all entries to log in')
            return
        
        # Host defaults to localhost
        if host == '':
            host = 'localhost'

        self.lock_login()


        # Getting the port via ICMP message
        try:
            scapy.all.send( scapy.all.IP(dst=host) / scapy.all.ICMP() / 'chat-request-port' )
            reply = scapy.all.sniff(
                filter = 'icmp',
                count = 1,
                lfilter = lambda p: 'chat-reply' in str(p), # we filter only packets containing this raw message
                timeout = TIMEOUT
            )
        except:
            self.display_message('[x] ERROR: host unknown')
            self.unlock_login()
            return
        
        if len(reply) == 0:
            self.display_message('[x] ERROR: server is busy or unreachable')
            self.unlock_login()
            return
        
        port = int(reply[0].load.lstrip('chat-reply-'))
        address = (host, port)


        print '[*] Login requested\n--> Host: %s\n--> Port: %s\n--> Username: %s' % (host, port, username)
        
        # Creating socket
        self.client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)

        # Trying to connect
        try:
            self.client_socket.connect(address)
        except s.error, e:
            if e[0] == 11004: # getaddrinfo failed
                self.display_message('[x] ERROR: host unknown')
            elif e[0] == 10061: # target machine actively refused
                self.display_message('[x] ERROR: server is busy or unreachable')
            else:
                self.display_message('[x] ERROR: ' + e[1])
            self.unlock_login()
            return
        except Exception, e:
            self.display_message('[x] ERROR: ' + str(e))

        # Username validation with the server
        self.client_socket.send(username)
        response = self.client_socket.recv(BUFFER_SIZE)
        if response == 'ok':
            self.display_message('[v] Logged in successfully as ' + username)
        else:
            self.display_message(response)
            self.unlock_login()
            return
        
        # Starting a listening thread
        self.unlock_chat()
        thread.start_new_thread(self.socket_listen, ())

    def socket_listen(self):
        '''
        Activates listening forever
        '''
        while True:

            # Recieve data from the server
            try:
                data = self.client_socket.recv(BUFFER_SIZE)
            except: break
            if not data: break
            
            # Handle commands from the server if given
            if data.startswith('/'):

                # Update online users in the online users list
                if data.startswith('/online'): # usernames are space-seperated
                    self.update_online_users(data.split()[1:])
                
                # Turn off the connection
                elif data.startswith('/off'):
                    self.logout()
                    return
            
            else:
                try:
                    self.display_message(data)
                except: pass
        
        self.display_message('[x] The connection with the server has been terminated.')
        self.unlock_login()
        self.lock_chat()

    def chat_sendmsg(self, event):
        '''
        Activates when the 'send' button is pressed,
        or when the user hits 'return' in the chat entry
        '''

        # Check if locked
        if self.locked_chat:
            return

        msg = self.submit_entry.get()
        if not msg: return

        self.submit_entry.delete(0, END)

        try:
            self.client_socket.send(msg)
        except s.error, e:
            print '[x] ERROR: ' + str(e)

        # Scroll to the bottom
        self.chat_list.yview_moveto(1.0)

    def logout(self):
        '''
        When logging out or when the current server shuts down.
        Performs log-out actions and reset to initial state
        '''
        self.chat_list.delete(0, END)
        self.update_online_users([])
        self.display_message('[x] Logged out.')
        self.lock_chat()
        self.unlock_login()


app = App()