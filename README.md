# Chat Room
Chat room with GUI using python tkinter, scapy, and sockets

Author: Daniel Peretz

## Features
* a live chat room
* everyone gets to choose a unique username
* see who's connected to the room at any time
* fun commands to play with

## Commands
* /time - Returns server time
* /rolladice - Rolls a dice and announces the result to everyone
* /quote - Quotes a random intelligent quote from a list of quotes
* /msg <username> <message ...> - Sends a private message to a user
* /logout - Logs you out as the user
* /shutdown <password> - Shuts down the server (if the password is correct)

## Troubleshooting
* If you get the message "host unknown" and you're sure that the host address is correct, then make sure scapy and winpcap are installed properly.
