# convert str into bytes
def string_to_bytes(data):
    return bytes(data, encoding='utf-8')


# convert bytes to string
def bytes_to_string(data):
    return data.decode("utf-8")


# find the user with given name in a list and return the user
def find_user(name, list_user):
    for user in list_user:
        if user.get_username() == name:
            return user
    return None

