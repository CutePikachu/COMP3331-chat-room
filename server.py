import sys
import re
import socket
from time import sleep
from threading import Timer, Lock
from User import User
from help_functions import *
from _thread import *


class Server:
    def __init__(self):
        self.users = []
        self._active_users = []
        self._block_duration = -1
        self._timeout = -1
        self._lock = Lock()

    def process_login(self, connection, client_add):
        while True:
            sleep(0.1)
            data = 'Username: '
            connection.sendall(string_to_bytes(data))
            username = bytes_to_string(connection.recv(16))

            curr_user = find_user(username, self.users)
            # if no such user or the user is current online, return error message
            if curr_user is None:
                connection.sendall(string_to_bytes("Username does not exist"))
                continue
            # if the user is active
            elif curr_user.is_active():
                connection.sendall(string_to_bytes(username + " is current online, please login another user."))
                continue

            # otherwise ask user to enter password
            data = 'Password: '

            connection.sendall(string_to_bytes(data))
            pwd = bytes_to_string(connection.recv(16))

            valid = 'False'
            for user in self.users:
                # check whether the user has been blocked for login
                # no need to process login for invalid user
                if username == user.get_username() and user.check_block():
                    connection.sendall(string_to_bytes("block"))
                    return False, username

                # validate the username and password
                if username == user.get_username() and user.validate_login(pwd):
                    user.login(connection, client_add)
                    user.timer_update()
                    valid = 'True'
                    break

            # if the username and pwd are valid or incorrect time less than 3
            # no need to block the user
            if curr_user.get_num_tries() < 3 or valid == "True":
                connection.sendall(string_to_bytes(valid))

            if valid == 'True':
                self.broadcast(string_to_bytes(username + " has logged in"), connection, curr_user)
                return True, username

            # block the user if it has been tried for equal or more than 3 times and still incorrect
            if curr_user.get_num_tries() >= 3 and valid != 'True':
                curr_user.block_user(self._block_duration)
                connection.sendall(string_to_bytes("block"))
                return False, username

    # process the command entered form user
    def process_command(self, connection, username):

        while True:
            try:
                command = bytes_to_string(connection.recv(1024)).rstrip('\n')
                curr_user = find_user(username, self.users)

                curr_user.timer_update()
                msgs = command.split(' ', 1)

                if re.match('logout', msgs[0].rstrip(' ')):
                    self.logout(username)
                elif re.match('message', msgs[0].rstrip(' ')):
                    receiver = msgs[1].split(' ', 1)[0]
                    message = msgs[1].split(' ', 1)[1]
                    self.messaging(username, receiver, message, connection)
                elif re.match('broadcast', msgs[0].rstrip(' ')):
                    message = username + "(broadcast): " + msgs[1]
                    self.broadcast(string_to_bytes(message), connection, curr_user)
                elif re.match('whoelse', msgs[0].rstrip(' ')):
                    list_user = self.who_else(username)
                    if list_user == "":
                        connection.sendall(string_to_bytes('Only u is active'))
                    else:
                        connection.sendall(string_to_bytes(list_user))
                elif re.match('whoelsesince', msgs[0]):
                    list_user = self.who_else_since(username, int(msgs[1]))
                    if list_user == "":
                        connection.sendall(string_to_bytes('Only u logged in since' + msgs[1]))
                    else:
                        connection.sendall(string_to_bytes(list_user))
                elif re.match('block', msgs[0]):
                    block_user = msgs[1]
                    self.block(username, block_user, connection)
                elif re.match('unblock', msgs[0]):
                    unblock_user = msgs[1]
                    self.unblock(username, unblock_user, connection)
                elif re.match('startprivate', msgs[0]):
                    peer_name = msgs[1].rstrip('\n')
                    find = False
                    block = False
                    for user in self._active_users:
                        if user['username'] == peer_name and peer_name != username:
                            find = True
                            # if the user is being blocked
                            # he shouldnt be connected
                            user_instance = find_user(username, self.users)
                            if user_instance.is_blocked(username):
                                connection.sendall(string_to_bytes(f"connection failed, {peer_name} has blocked you:)."))
                                block = True
                            else:
                                peer = find_user(peer_name, self.users)
                                # send address to client request for connection
                                connection.sendall(string_to_bytes(f"private_connection {peer.get_address()[0]} {peer.get_port_num()} {peer_name} {username}"))
                    if not find or not peer_name or not peer_name.strip():
                        connection.sendall(string_to_bytes("Error: peer " + peer_name + " is not valid"))
                elif re.match('port', msgs[0]):
                    port_num = msgs[1].rstrip('\n')
                    curr_user.set_port_num(port_num)
                else:
                    connection.sendall(string_to_bytes('In valid command ' + msgs[0]))
            except:
                continue

    # remove inactive user from the list
    def remove(self, con):
        connection = list(filter(lambda i: i['sock'] != con, self._active_users))
        self._active_users = connection

    # logout user
    def logout(self, username):
        user = find_user(username, self.users)
        connection = user.log_out()
        try: 
            connection.sendall(string_to_bytes("You have been logged out"))
            connection.close()
            sleep(0.1)
        except OSError:
            sleep(0.1)
        finally:
            self.broadcast(string_to_bytes(username + " left the chat"), connection, user)  
            self.remove(connection)

    # add a new user thread
    def add_user(self, connection, client_address):
        try:
            # process login
            status, username = self.process_login(connection, client_address)

            print("connection from ", client_address)
            # if the user doesnt login with a success
            if not status:
                connection.close()
            else:
                # keep track of user if login successfully
                # add user to the active user list
                self._active_users.append({'username': username, 'sock': connection})
                # resent offline messages
                curr_user = find_user(username, self.users)
                offline_message = curr_user.get_offline_messages()
                if offline_message:
                    for msg in offline_message:
                        connection.sendall(string_to_bytes(msg + '\n'))

                self.process_command(connection, username)

        finally:
            print('connection closed')

    # set up the server for listening
    def set_up(self, port_number):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', port_number)
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
                sys.exit(1)

    def timeout_user(self):
        Timer(1.0, self.timeout_user).start()
        for user in self.users:
            if user.check_timeout(self._timeout):
                self.logout(user.get_username())

    # send message to other user
    def messaging(self, sender, receiver, message, connection):
        receiver_con = find_user(receiver, self.users)
        message = "from " + sender + " : " + message
        if sender == receiver:
            connection.sendall(string_to_bytes(f"Error: you shouldn't message yourself."))
        elif not receiver_con:
            connection.sendall(string_to_bytes(f"Error: {receiver} is not available."))
        elif not receiver_con.is_active():
            receiver_con.store_offline_message(message)
        elif receiver_con.is_blocked(sender):
            connection.sendall(string_to_bytes(f"Error: your message won't be delievered as the recipient has blocked you."))
        else:
            receiver_con.get_connection().sendall(string_to_bytes(message))

    # list all online users
    def who_else(self, username):
        user_list = ""
        for user in self.users:
            if user.is_active() and user.get_username() != username:
                user_list = user_list + user.get_username() + " "
        return user_list

        # list all online users logged in the past time minutes

    def who_else_since(self, username, time):
        user_list = ""
        for user in self.users:
            if user.is_logged_in_after(time) and user.get_username() != username:
                user_list = user_list + user.get_username() + " "
        return user_list

    # broadcast msg to users
    def broadcast(self, message, connection, sender):
        # if the sender has blocked someone
        if sender.has_black_list():
            connection.sendall(string_to_bytes("Systen: warning. You have blocked some user who won't receive this "
                                               "message."))

        for user in self._active_users:
            # if the user is not themselves or blocks the sender
            # check the sender is not in the black list of receiver
            receiver = find_user(user['username'], self.users)
            if user['sock'] != connection and not receiver.is_blocked(sender.get_username()):
                try:
                    user['sock'].sendall(message)
                except:
                    user['sock'].close()
                    # if the user is no longer active, remove from the active list
                    self._active_users.remove(user)
            elif receiver.is_blocked(sender.get_username()):
                connection.sendall(string_to_bytes("Warning. Some user who won't receive this message."))

    # allow a user to block another user
    def block(self, username, block_name, connection):
        user = find_user(username, self.users)
        if user.block_user(block_name):
            connection.sendall(string_to_bytes(block_name + " has been blocked"))
        else:
            connection.sendall(string_to_bytes("Failed. You cannot block " + block_name))

    # allow a user to unblock another user
    def unblock(self, username, unblock_name, connection):
        user = find_user(username, self.users)
        if user.unblock_user(unblock_name):
            connection.sendall(string_to_bytes(unblock_name + " has been unblocked"))
        else:
            connection.sendall(string_to_bytes("Failed. You cannot unblock " + unblock_name))

    # read the credential file and create username pwd pair
    def read_credentials(self):
        content = [line.rstrip('\n') for line in open('Credentials.txt')]
        for item in content:
            self.users.append(User(item.split(' ')[0], item.split(' ')[1]))

    # main function to activate server
    def main(self):
        # process the command line args
        if len(sys.argv) < 4:
            print("Usage: python3 server.py [server_port] [block_duration] [timeout]")
            exit(1)
        elif not sys.argv[1].isdigit() or not sys.argv[2].isdigit() or not sys.argv[3].isdigit():
            print("server_port, block_duration and timeout should be numeric")

        port_number = int(sys.argv[1])
        self._block_duration = int(sys.argv[2])
        self._timeout = int(sys.argv[3])

        # create possible user lists
        self.read_credentials()

        # set up server
        self.set_up(port_number)


if __name__ == '__main__':
    server = Server()
    server.timeout_user()
    server.main()
