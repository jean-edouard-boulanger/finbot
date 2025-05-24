import tempfile
from typing import cast

import gnupg
from cryptography.fernet import Fernet


def fernet_generate_key() -> bytes:
    return Fernet.generate_key()


def fernet_encrypt(data: bytes, secret: bytes) -> bytes:
    fernet = Fernet(secret)
    return fernet.encrypt(data)


def fernet_decrypt(data: bytes, secret: bytes) -> bytes:
    fernet = Fernet(secret)
    return fernet.decrypt(data)


def pgp_decrypt(*, pgp_key_blob: bytes, passphrase: str | None, encrypted_blob: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as temp_dir:
        gpg = gnupg.GPG(gnupghome=temp_dir)
        import_result = gpg.import_keys(pgp_key_blob)
        assert import_result
        decrypted_data = gpg.decrypt(encrypted_blob, passphrase=passphrase)
        assert decrypted_data.ok
        return cast(bytes, decrypted_data.data)
