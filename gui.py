try:
    from Tkinter import *
except ImportError:
    from tkinter import *

import socket as s
import time, threading, thread, re

# GUI
PADDING = 12
MIN_WIDTH = 500
MIN_HEIGHT = 250

# NETWORK
PORT = 30000
BUFFER_SIZE = 1024

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

    def gui_setup_actions(self):
        '''
        Set up actions area
        '''

        self.side_frame = Frame(self.bottom_pwin, padx=PADDING, pady=PADDING)
        self.bottom_pwin.add(self.side_frame)

        self.online_label = Label(self.side_frame, text='Online users: 0')
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

    def unlock_login(self):
        '''
        Unocks (enables) the login entries, as well as the button.
        '''
        self.login_submit_button['state'] = NORMAL
        self.login_host_entry['state'] = NORMAL
        self.login_username_entry['state'] = NORMAL

    def display_message(self, msg):
        '''
        Displays the given message on the chat ListBox
        '''

        self.chat_list.insert(self.chat_list.size()+1, msg)

        col = 'black'
        if msg.startswith('[*]'):
            col = 'blue4'
        elif msg.startswith('[x]'):
            col = 'red4'
        elif msg.startswith('[v]'):
            col = 'green4'
        self.chat_list.itemconfig(self.chat_list.size()-1, {'fg': col})

    def login(self, event):
        '''
        Performs login actions, including verifying the username
        and connecting via sockets
        '''

        # Getting data from the entries
        host = self.login_host_entry.get()
        port = PORT
        username = self.login_username_entry.get()
        address = (host, port)

        # Validating input
        if host == '' or username == '':
            self.display_message('[x] ERROR: please fill all entries to log in')
            return

        self.lock_login()

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
            self.display_message('[x] ERROR: ' + e)

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
        thread.start_new_thread(self.socket_listen, ())

    def socket_listen(self):
        '''
        Activates listening forever
        '''
        while True:
            data = self.client_socket.recv(BUFFER_SIZE)
            if not data: break
            self.display_message(data)
        
        self.display_message('[x] The connection with the server has been terminated.')
        self.unlock_login()

    def chat_sendmsg(self, event):
        msg = self.submit_entry.get()
        if not msg: return
        self.submit_entry.delete(0, END)
        self.client_socket.send(msg)

app = App()