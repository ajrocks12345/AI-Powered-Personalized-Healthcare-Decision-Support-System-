#server.py
#pip install pycryptodome
import socket
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
# shared secret key (16 bytes)
key = b'1234567890abcdef'
s = socket.socket()
s.bind(("0.0.0.0", 5000))
s.listen(1)
conn, addr = s.accept()
print("Connected:", addr)
iv = conn.recv(16)
ciphertext = conn.recv(1024)
print("\n--- Server ---")
print("IV received (hex):", iv.hex())
print("Ciphertext received (hex):", ciphertext.hex())
cipher = AES.new(key, AES.MODE_CBC, iv)
plaintext = unpad(cipher.decrypt(ciphertext), 16)
print("Decrypted message:", plaintext.decode())
conn.close()
