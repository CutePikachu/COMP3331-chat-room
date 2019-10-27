import select
import socket
import sys

from help_functions import *


# user logged out
def log_out(server):
    print("bye")
    server.close()
    exit(0)


# process the message receiver from server
def process_message_received(server, msg):
    if msg == string_to_bytes("You have been logged out"):
        print("You have been logged out")
        log_out(server)


# process different command typed by user
def process_message_typed(server, msg):
    if msg == "logout":
        print("bye")
        server.close()
        exit(0)


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
                server.send(string_to_bytes(message))
                process_message_typed(server, message)


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
