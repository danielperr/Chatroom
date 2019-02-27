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

class App:

    def __init__(self):

        self.root = Tk()

        self.root.update()
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

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
        self.login_host_label.pack(side=LEFT, expand=1, fill=X)
        self.login_host_entry = Entry(self.login_frame)
        self.login_host_entry.pack(side=LEFT, expand=1, fill=X)

        # Username entry
        self.login_username_label = Label(self.login_frame, text='Username: ')
        self.login_username_label.pack(side=LEFT, expand=1, fill=X)
        self.login_username_entry = Entry(self.login_frame)
        self.login_username_entry.pack(side=LEFT, expand=1, fill=X)

        # Connect button
        self.login_submit_button = Button(self.login_frame, text='Connect')
        self.login_submit_button.pack(side=LEFT, expand=1, fill=X)

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

        self.login_submit_button.bind('<ButtonRelease-1>', self.login)
        self.submit_button.bind('<ButtonRelease-1>', self.chat_sendmsg)

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
        
        self.chat_list.itemconfig(self.chat_list.size()-1, kwargs)

    def login(self, event):

        # Lock the button and the entries

        host = self.login_host_entry.get()
        port = PORT
        username = self.login_username_entry.get()
        address = (host, port)

        print '[*] Login requested\n--> Host: %s\n--> Port: %s\n--> Username: %s' % (host, port, username)

        self.client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.client_socket.connect(address)

        # Username validation with the server
        self.client_socket.send(username)
        response = self.client_socket.recv(BUFFER_SIZE)
        if response == 'ok':
            self.display_message('Logged in successfully as ' + username, fg='green4')
        else:
            self.display_message('ERROR: Username %s already exists!' % username, fg='red4')
            # Unlock the button and the entries
            return
        
        thread.start_new_thread(self.socket_listen, ())

    def socket_listen(self):
        '''
        Activates recieve listening forever
        '''
        while True:
            data = self.client_socket.recv(BUFFER_SIZE)
            if not data: break
            self.display_message(data)

    def chat_sendmsg(self, event):
        msg = self.submit_entry.get()
        if not msg:
            return
        self.client_socket.send(msg)

app = App()