from bcrypt import hashpw, gensalt, checkpw


def hash_password(password:str):
    password = password.encode()
    password = hashpw(password, salt=gensalt())
    return password.decode()

def check_password(password: str, hashed_password: str):
    return  checkpw(password.encode(), hashed_password.encode())