import boto3
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# AWS Secrets Manager Client

SECRET_KEY = os.getenv("ENCRYPTION_KEY")

def get_encryption_key():
    """Fetch encryption key from AWS Secrets Manager."""
    return bytes.fromhex(SECRET_KEY)

def encrypt_message(message):
    """Encrypt a message using AES-256."""
    key = get_encryption_key()
    iv = os.urandom(16)  # Generate a new IV for every message
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    
    # Pad the message to 16 bytes
    padded_message = message + " " * (16 - len(message) % 16)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_message.encode("utf-8")) + encryptor.finalize()
    
    # Store IV + Ciphertext
    return base64.b64encode(iv + ciphertext).decode("utf-8")

def decrypt_message(encrypted_message):
    """Decrypt a message using AES-256."""
    key = get_encryption_key()
    encrypted_data = base64.b64decode(encrypted_message)
    
    iv = encrypted_data[:16]  # Extract IV
    ciphertext = encrypted_data[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_text = decryptor.update(ciphertext) + decryptor.finalize()
    
    return decrypted_text.decode("utf-8").strip()  # Remove padding
