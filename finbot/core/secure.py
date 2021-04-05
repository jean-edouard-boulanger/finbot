from cryptography.fernet import Fernet


def fernet_generate_key() -> bytes:
    return Fernet.generate_key()


def fernet_encrypt(data: bytes, secret: bytes) -> bytes:
    fernet = Fernet(secret)
    return fernet.encrypt(data)


def fernet_decrypt(data: bytes, secret: bytes) -> bytes:
    fernet = Fernet(secret)
    return fernet.decrypt(data)
