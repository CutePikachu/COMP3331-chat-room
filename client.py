import select
import socket
import sys
from _thread import start_new_thread

from help_functions import *

# the user list of p2p connections
p2p_users = []


# get message from peer
def p2p_messaging(connection, peer_name):
    while True:
        try:
            msg = bytes_to_string(connection.recv(1024))
            print(msg)
        except:
            continue


# receive connection from peer
def p2p_connection(sock, client_address):
    try:
        # get username from peer
        peer_name = sock.recv(1024)
        # add user to list
        global p2p_users
        p2p_users.append({'peer_name': peer_name, 'sock': sock})

        p2p_messaging(sock, peer_name)
        print("connection from ", peer_name)

    finally:
        print('connection closed from ', peer_name)


def listen_for_connection():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind('localhost', 30000)
    sock.listen(1)
    while True:
        print("Waiting for connection...")
        connection, client_address = sock.accept()
        start_new_thread(p2p_connection, (connection, client_address))


# user logged out
def log_out(server):
    print("bye")
    server.close()
    exit(0)


# process the message receiver from server
def process_message_received(server, msg):
    global p2p_users
    if msg == string_to_bytes("You have been logged out"):
        print("You have been logged out")
        log_out(server)
    elif msg.split(' ', 1)[0].rstrip(' ') == string_to_bytes("stopprivate"):
        peer = msg.split(' ', 1)[1]
        con = None
        
        for p in p2p_users[peer]:
            if p['peer_name'] == peer:
                con = p['sock']
                connection = list(filter(lambda i: i['sock'] != con, p2p_users))
                p2p_users = connection
                con.close()
    elif msg.split(' ', 1)[0].rstrip(' ') == string_to_bytes("private_connection"):
        peer_ip = msg.split(' ', 2)[1].rstrip(' ')
        peer_port = msg.split(' ', 3)[2].rstrip(' ')
        peer_name = msg.split(' ', 3)[3].rstrip('\n')
        # connect to the new peer using a new socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_address = (peer_ip, peer_port)
        # client connect to peer and add peer to list
        sock.connect(peer_address)

        p2p_users.append({'peer_name': peer_name, 'sock': sock})
        # listen from peer
        p2p_messaging(sock, peer_name)


# process different command typed by user
def process_message_typed(server, msg):
    if msg == "logout":
        return "logout"
    # if the message is private messaging
    elif msg.split(' ', 1)[0] == "private":
        peer = msg.split(' ', 2)[1].rstrip(' ')
        message = msg.split(' ', 2)[2]
        # send message to peer
        global p2p_users
        p2p_users[peer].sendall(string_to_bytes(message))
    return 'not private'


# while the user is online, it can send command to the server
def online_user(server):
    while True:
        sockets_list = [sys.stdin, server]
        read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])
        for socks in read_sockets:
            if socks == server:
                message = socks.recv(2048)
                process_message_received(server, message)
                print(bytes_to_string(message))
            else:
                message = sys.stdin.readline()
                result = process_message_typed(server, message)
                if result == 'logout':
                    log_out(server)
                elif result != 'private':
                    server.send(string_to_bytes(message))


# user enter use name and password for login validation
def login(sock):
    while True:
        try:
            # send username and password to server
            print(bytes_to_string(sock.recv(16)))
            username = sys.stdin.readline().rstrip()
            sock.sendall(string_to_bytes(username))

            # get the message from server
            msg = bytes_to_string(sock.recv(1024))

            # if it is not password
            # print the error message and restart the loop

            if msg != 'Password: ':
                valid = string_to_bytes('error before entering pwd')
                continue
            else:
                print(msg)
                pwd = sys.stdin.readline().rstrip()
                sock.sendall(string_to_bytes(pwd))
                valid = sock.recv(16)

        finally:
            if bytes_to_string(valid) == 'True':
                print('Login successfully...')
                # client listening on its port when it is login successfully
                start_new_thread(listen_for_connection, (sock, ))
                # client sending message to server
                online_user(sock)
                exit(1)
            elif bytes_to_string(valid) == 'False':
                print("Invalid password, please try again")
            elif bytes_to_string(valid) == 'error before entering pwd':
                print(msg)
            else:
                print("You have been blocked, please try again later")
                print(valid)
                sock.close()
                exit(1)


# set up the client connection
def set_up(server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (server_ip, server_port)
    # client connect to server
    sock.connect(server_address)
    print("Connecting to server...")
    login(sock)


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


if __name__ == '__main__':
    main()
