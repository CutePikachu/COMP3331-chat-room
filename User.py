import time


class User:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._sock = None
        self._login = False
        self._start_time = -1
        self._timer = 0
        self._block = -1
        self._num_tries = 0
        self._black_list = []
        self._offline_messages = []

    # getters
    def get_username(self):
        return self._username

    def get_num_tries(self):
        return self._num_tries

    def get_connection(self):
        return self._sock

    # check username and pwd are match
    def validate_login(self, password):
        self._num_tries += 1
        if self._password == password and self._num_tries < 3:
            return True
        return False

    # log out user status
    def log_out(self):
        self._login = False
        return self._sock

    # start timer
    def timer_update(self):
        self._timer = time.time()

    # block the user
    def block_user(self, block_time):
        self._block = time.time() + block_time
        self._num_tries = 0

    def check_block(self):
        if self._block < time.time():
            return False
        else:
            self._block = -1
            return True

    # check time out
    def check_timeout(self, timeout):
        if self._login and (self._timer + timeout) < time.time():
            return True
        return False

    # login the user
    def login(self, connection):
        self._num_tries = 0
        self._sock = connection
        self._timer = self._start_time = time.time()
        self._login = True

    # check whether the user is active
    def is_active(self):
        return self._login

    # add the user to black list
    def block_user(self, user):
        if user not in self._black_list:
            self._black_list.append(user)
            return True
        return False

    # remove user from black list
    def unblock_user(self, user):
        if user in self._black_list:
            self._black_list.remove(user)
            return True
        return False

    # check whether the given user is blocked by the current user
    def is_blocked(self, user):
        return user in self._black_list

    # whether the user is logged in in the past time secs
    def is_logged_in_after(self, secs):
        return self._start_time + secs >= time.time()