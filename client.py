import select
import socket, errno
import sys
from time import sleep

from _thread import start_new_thread
from help_functions import *

username = ''
server = None
peers = []


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 client.py [server_IP] [server_port]")
        sys.exit(1)
    elif not sys.argv[2].isdigit():
        print("Invalid server IP address or server port")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    set_up(server_ip, server_port)


# set up the client connection
def set_up(server_ip, server_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (server_ip, server_port)
        # client connect to server
        sock.connect(server_address)
        print("system: Connecting to server...")
        global server
        server = sock
        login()
    except ConnectionRefusedError:
        print("System: connnection failed")


# user enter use name and password for login validation
def login():
    while True:
        try:
            # send username and password to server
            global server, username
            print(bytes_to_string(server.recv(1024)))
            username = sys.stdin.readline().rstrip()
            server.sendall(string_to_bytes(username))

            # get the message from server
            msg = bytes_to_string(server.recv(1024))

            # if it is not password
            # print the error message and restart the loop

            if msg != 'Password: ':
                valid = string_to_bytes('error before entering pwd')
                continue
            else:
                print(msg)
                pwd = sys.stdin.readline().rstrip()
                server.sendall(string_to_bytes(pwd))
                valid = server.recv(16)

        finally:
            if bytes_to_string(valid) == 'True':
                print('system: Login successfully...')
                username = username
                # client listening on its port when it is login successfully
                start_new_thread(listen_for_connection, (server,))
                # client sending message to server
                online_user(server)
                exit(1)
            elif bytes_to_string(valid) == 'False':
                print("Error: Invalid password, please try again")
            elif bytes_to_string(valid) == 'error before entering pwd':
                print(msg)
            else:
                print("System: You have been blocked, please try again later")
                server.close()
                exit(1)


# listen from keyboard
def listen_from_keyboard(connection):
    global server
    while True:
        try:
            message = sys.stdin.readline()
            result = process_message_typed(connection, message)
            if result == 'logout':
                log_out()
            elif result != 'private':
                server.send(string_to_bytes(message)) if server else print(
                    "Error: Invalid client server message, you are disconnected with the server.")
            elif connection:
                try:
                    connection.send(string_to_bytes(message))
                except OSError:
                    return
        except KeyboardInterrupt:
            sys.exit(1)


# while the user is online, it can send command to the server
def online_user(connection):
    global server
    start_new_thread(listen_from_keyboard, (None,))
    while True:
        try:
            if not server:
                return
            message = server.recv(2048)
            if not message:
                print('\nsystem: Disconnected from server')
                return
            if process_message_received(server, message):
                print(bytes_to_string(message))

        except KeyboardInterrupt:
            log_out()


# process the message receiver from server
def process_message_received(con, msg):
    global peers
    if not peers:
        peers = []
    msg = bytes_to_string(msg)
    if msg == "You have been logged out":
        log_out()
    elif msg.split(' ', 1)[0].rstrip(' ') == "stopprivate":
        print("\"" + msg.split(' ', 1)[0].rstrip(' ') + "\"" + " receive")
        stop_private(msg.split(' ', 1)[1])
    elif msg.split(' ', 1)[0].rstrip(' ') == "private_connection":
        peer_ip = msg.split(' ', 4)[1].rstrip(' ')
        peer_port = msg.split(' ', 4)[2].rstrip(' ')
        peer_name = msg.split(' ', 4)[3].rstrip(' ')
        name = msg.split(' ', 4)[4].rstrip(' ')

        # connect to the new peer using a new socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_address = (peer_ip, int(peer_port))
        # client connect to peer and add peer to list
        sock.connect(peer_address)
        peers.append({'peer_name': peer_name, 'sock': sock})
        # send name to peer
        sock.sendall(string_to_bytes(username))
        print("system: connected to " + peer_ip + " peer name is " + peer_name + " username is " + name)
        # listen from peer
        start_new_thread(p2p_messaging, (sock, peer_name))
        return False
    return True


# process different command typed by user
# determine whether it is private
def process_message_typed(server, msg):
    global peers, username
    if msg == "logout":
        return "logout"
    # if the message is private messaging
    elif msg.split(' ', 1)[0].rstrip(' ') == "private":

        peer_name = msg.split(' ', 2)[1].rstrip(' ')
        message = username + "(private): " + msg.split(' ', 2)[2]
        # if there is no peer connected
        if not peers:
            peers = []
            print(f"system: error. You haven't established an connection with {peer_name}.")
            return "private"
        find = False
        # send message to peer
        for peer in peers:
            if peer['peer_name'] == peer_name:
                find = True
                peer['sock'].sendall(string_to_bytes(message))
        if not find:
            print(f"system: error. You haven't established an connection with {peer_name}.")
        return 'private'
    elif msg.split(' ', 1)[0].rstrip(' ') == "stopprivate":
        peer_name = msg.split(' ', 2)[1].rstrip(' ')
        # if there is no peer connected
        if not peers:
            peers = []
            print(f"system: error. You haven't established an connection with {peer_name}.")
            return "private"
        find = False
        peer = msg.split(' ', 1)[1].rstrip(' ')
        # find the peer to close connection

        for p in peers:
            if p['peer_name'] == peer.rstrip("\n"):
                print("system: stop connection from " + peer)
                find = True
                con = p['sock']
                con.sendall(string_to_bytes("stopprivate " + username))
                con.close()
                peers = peers.remove(p)
                break
        # error message for not find peer
        if not find:
            print(f"system: error. You haven't established an connection with {peer_name}.")
        return 'private'
    elif msg.strip() == "startprivate":
        print("system: error, peer name should not be empty.")
        return "private"
    elif msg.split(' ', 1)[0].rstrip(' ') == 'startprivate':
        peer_name = msg.split(' ', 1)[1].rstrip(' ')
        if not peers:
            peers = []
        for peer in peers:
            if peer['peer_name'] == peer_name:
                print(f"system: error. You have already connected with {peer_name}.")
                return 'private'
    return 'not private'


# create listening socket to listen from other peers
def listen_for_connection(con):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = find_available_port(sock)
    con.sendall(string_to_bytes('port ' + str(port)))
    sleep(0.1)
    sock.listen(5)
    while True:
        print("system: Waiting for connection...")
        connection, client_address = sock.accept()
        start_new_thread(p2p_connection, (connection, client_address))


def stop_private(peer):
    print("system: stop private connection")
    global peers
    # close the connection
    if not peers:
        peers = []
    for p in peers:
        if p['peer_name'] == peer.rstrip("\n"):
            print("stop connection from " + peer)
            con = p['sock']
            con.close()
            peers = peers.remove(p)
            if not peers:
                peers = []


# user logged out
def log_out():
    print("System: bye")
    global server
    # tell server to logout
    server.sendall(string_to_bytes('logout'))
    # close connection with server
    server.close()
    server = None
    sys.exit(1)


def find_available_port(sock):
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


# get message from peer
def p2p_messaging(connection, peer_name):
    start_new_thread(listen_from_keyboard, (connection,))
    while True:
        try: 
            message = connection.recv(2048)
            msg = bytes_to_string(message)
            if msg.split(' ', 1)[0].rstrip(' ') == "stopprivate":
                stop_private(msg.split(' ', 1)[1].rstrip(' '))
                break
            print(bytes_to_string(message))
        except OSError:
            return 


# receive connection from peer
def p2p_connection(sock, client_address):
    global peers
    if not peers:
        peers = []
    try:
        print('system: ready to get name')
        # get username from peer
        peer_name = bytes_to_string(sock.recv(1024))
        print("system: get name")

        # add user to list
        peers.append({'peer_name': peer_name, 'sock': sock})

        print("system: connection from ", peer_name)
        p2p_messaging(sock, peer_name)
    finally:
        print('system: connection closed from ', peer_name)


if __name__ == '__main__':
    main()
