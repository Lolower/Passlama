from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# Функції для шифрування
def encrypt_password(password: str, key: bytes) -> str:
    """Шифрування пароля з використанням AES-256-CBC"""
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padding_length = AES.block_size - len(password) % AES.block_size
    padded_password = password + chr(padding_length) * padding_length
    ciphertext = cipher.encrypt(padded_password.encode('utf-8'))
    return base64.b64encode(iv + ciphertext).decode('utf-8')


def decrypt_password(encrypted_password: str, key: bytes) -> str:
    """Розшифрування пароля"""
    encrypted_data = base64.b64decode(encrypted_password)
    iv = encrypted_data[:AES.block_size]
    ciphertext = encrypted_data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(ciphertext)
    padding_length = decrypted_data[-1]
    return decrypted_data[:-padding_length].decode('utf-8')
