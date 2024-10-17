from cryptography.fernet import Fernet
import os
from config import Config
from logger import logger

def generate_key():
    key = Fernet.generate_key()
    os.makedirs(os.path.dirname(Config.AES_KEY_FILE), exist_ok=True)
    with open(Config.AES_KEY_FILE, 'wb') as key_file:
        key_file.write(key)
    logger.info('AES encryption key generated.')
    return key

def load_key():
    if not os.path.exists(Config.AES_KEY_FILE):
        return generate_key()
    with open(Config.AES_KEY_FILE, 'rb') as key_file:
        key = key_file.read()
    return key

def encrypt_file(file_path):
    key = load_key()
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        original = file.read()
    encrypted = fernet.encrypt(original)
    with open(file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)
    logger.info(f'File encrypted: {file_path}')

def decrypt_file(file_path):
    key = load_key()
    fernet = Fernet(key)
    with open(file_path, 'rb') as enc_file:
        encrypted = enc_file.read()
    decrypted = fernet.decrypt(encrypted)
    with open(file_path, 'wb') as dec_file:
        dec_file.write(decrypted)
    logger.info(f'File decrypted: {file_path}')
