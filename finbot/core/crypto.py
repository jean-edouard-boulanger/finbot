from cryptography.fernet import Fernet


def fernet_generate_key():
    return Fernet.generate_key()


def fernet_encrypt(data, secret=None):
    fernet = Fernet(secret)
    return fernet.encrypt(data)


def fernet_decrypt(data, secret):
    fernet = Fernet(secret)
    return fernet.decrypt(data)
