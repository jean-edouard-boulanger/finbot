import tempfile
from typing import AnyStr, cast

import gnupg
import orjson
from cryptography.fernet import Fernet

from finbot.core.async_ import aexec
from finbot.core.typing_extensions import JSON


def _to_bytes(data: AnyStr) -> bytes:
    return data if isinstance(data, bytes) else data.encode()


def fernet_generate_key() -> bytes:
    return Fernet.generate_key()


def fernet_encrypt(data: AnyStr, secret: AnyStr) -> bytes:
    fernet = Fernet(_to_bytes(secret))
    return fernet.encrypt(_to_bytes(data))


def fernet_decrypt(data: AnyStr, secret: AnyStr) -> bytes:
    fernet = Fernet(_to_bytes(secret))
    return fernet.decrypt(_to_bytes(data))


def fernet_encrypt_json(payload: JSON, secret: AnyStr) -> bytes:
    return fernet_encrypt(orjson.dumps(payload), secret)  # type: ignore


def fernet_decrypt_json(encrypted_json: AnyStr, secret: AnyStr) -> JSON:
    return cast(JSON, orjson.loads(fernet_decrypt(encrypted_json, secret)))


def pgp_decrypt(*, pgp_key_blob: bytes, passphrase: str | None, encrypted_blob: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as temp_dir:
        gpg = gnupg.GPG(gnupghome=temp_dir)
        import_result = gpg.import_keys(pgp_key_blob)
        assert import_result
        decrypted_data = gpg.decrypt(encrypted_blob, passphrase=passphrase)
        assert decrypted_data.ok
        return cast(bytes, decrypted_data.data)


async def async_pgp_decrypt(pgp_key_blob: bytes, passphrase: str | None, encrypted_blob: bytes) -> bytes:
    return await aexec(
        pgp_decrypt,
        pgp_key_blob=pgp_key_blob,
        passphrase=passphrase,
        encrypted_blob=encrypted_blob,
    )
