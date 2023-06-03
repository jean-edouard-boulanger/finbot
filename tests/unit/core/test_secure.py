from finbot.core import secure


def test_encryption_workflow():
    fernet_key = secure.fernet_generate_key()
    assert isinstance(fernet_key, bytes)
    test_data = "hello world"
    encrypted_data = secure.fernet_encrypt(test_data.encode(), fernet_key)
    assert isinstance(encrypted_data, bytes)
    decrypted_data = secure.fernet_decrypt(encrypted_data, fernet_key)
    assert isinstance(decrypted_data, bytes)
    assert decrypted_data.decode() == test_data
