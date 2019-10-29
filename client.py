import select
import socket, errno
import sys
from time import sleep
from _thread import start_new_thread

from help_functions import *


sername = ''
server = None
peers = []

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 client.py [server_IP] [server_port]")
        exit(1)
    elif not sys.argv[2].isdigit():
        print("Invalid server IP address or server port")
        exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    set_up(server_ip, server_port)

    # set up the client connection
def set_up(server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (server_ip, server_port)
    # client connect to server
    sock.connect(server_address)
    print("Connecting to server...")
    global server
    server = sock
    login()


# user enter use name and password for login validation
def login():
    while True:
        try:
            # send username and password to server
            print(bytes_to_string(_server.recv(1024)))
            username = sys.stdin.readline().rstrip()
            _server.sendall(string_to_bytes(username))

            # get the message from server
            msg = bytes_to_string( _server.recv(1024))

            # if it is not password
            # print the error message and restart the loop

            if msg != 'Password: ':
                valid = string_to_bytes('error before entering pwd')
                continue
            else:
                print(msg)
                pwd = sys.stdin.readline().rstrip()
                _server.sendall(string_to_bytes(pwd))
                valid = _server.recv(16)

        finally:
            if bytes_to_string(valid) == 'True':
                print('Login successfully...')
                username = username
                # client listening on its port when it is login successfully
                start_new_thread(listen_for_connection, (_server,))
                # client sending message to server
                online_user(_server)
                exit(1)
            elif bytes_to_string(valid) == 'False':
                print("Invalid password, please try again")
            elif bytes_to_string(valid) == 'error before entering pwd':
                print(msg)
            else:
                print("You have been blocked, please try again later")
                print(valid)
                _server.close()
                exit(1)

# while the user is online, it can send command to the server
def online_user(connection):
    while True:
        sockets_list = [sys.stdin, connection]
        read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])
        for socks in read_sockets:
            if socks == connection:
                message = socks.recv(2048)
                process_message_received(connection, message)
                print(bytes_to_string(message))
            else:
                message = sys.stdin.readline()
                result = process_message_typed(connection, message)
                if result == 'logout':
                    log_out()
                elif result != 'private':
                    _server.send(string_to_bytes(message))

# process the message receiver from server
def process_message_received(server, msg):
    msg = bytes_to_string(msg)
    if msg == "You have been logged out":
        print(msg)
        log_out()
    elif msg.split(' ', 1)[0].rstrip(' ') == "stopprivate":
        stop_private(msg.split(' ', 1)[1])       
    elif msg.split(' ', 1)[0].rstrip(' ') == "private_connection":
        peer_ip = msg.split(' ', 4)[1].rstrip(' ')
        peer_port = msg.split(' ', 4)[2].rstrip(' ')
        peer_name = msg.split(' ', 4)[3].rstrip(' ')
        username = msg.split(' ', 4)[4].rstrip(' ')

        # connect to the new peer using a new socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_address = (peer_ip, int(peer_port))
        # client connect to peer and add peer to list
        sock.connect(peer_address)
        
        print(type())
        # peers.append({'peer_name': peer_name, 'sock': sock})
        # send name to peer
        sock.sendall(string_to_bytes(username))
        print("connected to " + peer_ip + " peer name is " + peer_name + " username is " + username)
        # listen from peer
        p2p_messaging(server, sock, peer_name)
    elif msg.split(' ', 1)[0].rstrip(' ') == "stopprivate":
        stop_private(msg.split(' ', 1)[1].rstrip(' '))

# process different command typed by user
def process_message_typed(server, msg):
    if msg == "logout":
        return "logout"
    # if the message is private messaging
    elif msg.split(' ', 1)[0].rstrip(' ') == "private":
        
        peer = msg.split(' ', 2)[1].rstrip(' ')
        message = msg.split(' ', 2)[2]
        # send message to peer

        for peer in peers:
            if peer['peer_name'] == peer:
                peer['sock'].sendall(string_to_bytes(message))
        return 'private'
    elif msg.split(' ', 1)[0].rstrip(' ') == "stopprivate":
        stop_private(msg.split(' ', 1)[1].rstrip(' '))
    return 'not private'

# create listening socket to listen from other peers
def listen_for_connection(server):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = find_availble_port(sock)
    server.sendall(string_to_bytes('port ' + str(port)))
    sleep(0.1)
    sock.listen(1)
    while True:
        print("Waiting for connection...")
        connection, client_address = sock.accept()
        start_new_thread(p2p_connection, (connection, client_address))
        
def stop_private(peer):
    # close the connection
    for p in peers[peer]:
        if p['peer_name'] == peer:
            con = p['sock']
            connection = list(filter(lambda i: i['sock'] != con, peers))
            peers = connection
            con.close()

# user logged out
def log_out():
    print("bye")
    # tell server to logout
    _server.sendall(string_to_bytes('logout'))
    # close connection with server
    _server.close()
    # close connection with all peers
    for peer in peers:
        peer['sock'].sendall(string_to_bytes('stopprivate ' + username))
        peer['sock'].close()
    peers = []
    exit(0)

def find_availble_port(sock):
    port_num = 3000
    while True:
        try:
            sock.bind(("127.0.0.1", port_num))
            return port_num
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                port_num += 1
            else:
                # something else raised the socket.error exception
                print(e)
                exit(1)
    return -1

# get message from peer
def p2p_messaging(connection, peer_name):
    while True:
        sockets_list = [sys.stdin, connection, _server]
        read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])
        for socks in read_sockets:
            if socks == connection:
                message = socks.recv(2048)
                print(bytes_to_string(message))
            elif socks == _server:
                message = socks.recv(2048)
                process_message_received(_server, message)
                print(bytes_to_string(message))
            else:
                message = sys.stdin.readline()
                result = process_message_typed(server, message)
                if result == 'logout':
                    log_out()
                elif result == 'not private':
                    _server.send(string_to_bytes(message))


# receive connection from peer
def p2p_connection(self, sock, client_address):
    try:
        print('ready to get name')
        # get username from peer
        peer_name = sock.recv(1024)
        print("get name")

        # add user to list
        peers.append({'peer_name': bytes_to_string(peer_name), 'sock': sock})
        
        print("connection from ", peer_name)
        p2p_messaging(sock, peer_name)
    finally:
        print('connection closed from ', peer_name)



if __name__ == '__main__':
    main()
