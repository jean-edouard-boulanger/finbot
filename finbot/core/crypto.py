from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


def _get_encryption_settings():
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )


def fernet_generate_key():
    return Fernet.generate_key()


def fernet_encrypt(data, secret=None):
    fernet = Fernet(secret)
    return fernet.encrypt(data)


def fernet_decrypt(data, secret):
    fernet = Fernet(secret)
    return fernet.decrypt(data)


def load_public_key(file_path):
    with open(file_path, "rb") as kf:
        return serialization.load_pem_public_key(
            kf.read(), 
            backend=default_backend())


def load_private_key(file_path, password=None):
    with open(file_path, "rb") as kf:
        return serialization.load_pem_private_key(
            kf.read(), 
            password=password,
            backend=default_backend())


def encrypt(data, public_key):
    return public_key.encrypt(data, _get_encryption_settings())


def decrypt(data, private_key):
    return private_key.decrypt(data, _get_encryption_settings())
