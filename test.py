import sys
import re
import socket
from time import sleep
from threading import Timer, Lock
from User import User
from help_functions import *
from _thread import *

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('129.94.209.42', 2000)
sock.bind(server_address)
print("The server has been set up.")
sock.listen(5)

# connect with client
while True:
    try:
        print("Waiting for connection...")
        connection, client_address = sock.accept()
        start_new_thread(self.add_user, (connection, client_address))
    except KeyboardInterrupt:
        exit(1)
