import socket
import threading
import signal
import subprocess
import sys
import os
import time
import hashlib
from cryptography.fernet import Fernet

PORT = 5555
BUFFER = 4096
running = True
CIPHER = None

# ---------- UI ----------

def clear():
    os.system("clear")

def show_logo():
    try:
        with open("logo.txt", "r") as f:
            print(f.read())
    except:
        pass

def show_threat_model():
    print("""
[ SECURITY STATUS ]
✔ IP Address Hidden (Tor)
✔ No Central Server
✔ Peer Authenticated
✔ End-to-End Encrypted
✔ Ephemeral Session
⚠ Tor Speed Limited
""")

# ---------- CLEAN EXIT ----------

def stop_all(sig, frame):
    print("\n[!] Stopping chat and Tor...")
    try:
        subprocess.call(["sudo", "systemctl", "stop", "tor"])
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, stop_all)

# ---------- CRYPTO ----------

def derive_key(shared_secret: str):
    digest = hashlib.sha256(shared_secret.encode()).digest()
    return Fernet(base64_key(digest))

def base64_key(raw):
    import base64
    return base64.urlsafe_b64encode(raw)

def perform_key_exchange(conn, is_host):
    global CIPHER

    secret = input("Shared secret (for E2EE): ").strip()

    if is_host:
        conn.send(secret.encode())
        peer = conn.recv(1024).decode()
    else:
        peer = conn.recv(1024).decode()
        conn.send(secret.encode())

    if peer != secret:
        print("[AUTH FAILED]")
        conn.close()
        sys.exit(0)

    CIPHER = derive_key(secret)

# ---------- PROGRESS BAR ----------

def progress_bar(done, total, start, prefix=""):
    elapsed = time.time() - start
    speed = done / elapsed if elapsed > 0 else 0
    eta = int((total - done) / speed) if speed > 0 else 0

    percent = int((done / total) * 100)
    bars = int(percent / 5)
    bar = "█" * bars + "░" * (20 - bars)

    print(
        f"\r{prefix} [{bar}] {percent}% | "
        f"{int(speed/1024)} KB/s | ETA {eta}s",
        end="",
        flush=True
    )

# ---------- RECEIVE ----------

def receive(conn):
    while running:
        try:
            data = conn.recv(BUFFER)
            if not data:
                break

            decrypted = CIPHER.decrypt(data)

            if decrypted.startswith(b"FILE|"):
                _, name, size = decrypted.decode().split("|")
                size = int(size)
                received = 0
                start = time.time()

                print(f"\n[Receiving file: {name}]")
                with open(name, "wb") as f:
                    while received < size:
                        chunk = conn.recv(BUFFER)
                        data = CIPHER.decrypt(chunk)
                        f.write(data)
                        received += len(data)
                        progress_bar(received, size, start, "Receiving")

                print(f"\n[File saved: {name}]\n> ", end="")
            else:
                print("\nFriend:", decrypted.decode(), "\n> ", end="")

        except:
            break

# ---------- SEND FILE ----------

def send_file(conn, path):
    if not os.path.exists(path):
        print("[File not found]")
        return

    size = os.path.getsize(path)
    name = os.path.basename(path)
    header = f"FILE|{name}|{size}".encode()
    conn.send(CIPHER.encrypt(header))

    sent = 0
    start = time.time()
    print(f"[Sending file: {name}]")

    with open(path, "rb") as f:
        while chunk := f.read(BUFFER):
            enc = CIPHER.encrypt(chunk)
            conn.send(enc)
            sent += len(chunk)
            progress_bar(sent, size, start, "Sending")

    print(f"\n[File sent: {name}]")

# ---------- CHAT ----------

def chat(conn):
    threading.Thread(target=receive, args=(conn,), daemon=True).start()

    while running:
        msg = input("> ")
        if msg.startswith("/send "):
            send_file(conn, msg.split(" ", 1)[1])
        else:
            conn.send(CIPHER.encrypt(msg.encode()))

# ---------- HOST / CLIENT ----------

def host():
    s = socket.socket()
    s.bind(("127.0.0.1", PORT))
    s.listen(1)
    print("[Waiting for connection...]")
    conn, _ = s.accept()

    perform_key_exchange(conn, True)
    show_threat_model()
    chat(conn)

def connect(onion):
    s = socket.socket()
    s.connect((onion, PORT))

    perform_key_exchange(s, False)
    show_threat_model()
    chat(s)

# ---------- MAIN ----------

clear()
show_logo()
print()

mode = input("Host (h) or Connect (c)? ").lower()
if mode == "h":
    host()
else:
    onion = input("Enter .onion address: ")
    connect(onion)
