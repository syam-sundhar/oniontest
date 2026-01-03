import socket
import threading
import signal
import subprocess
import sys
import os
import time

PORT = 5555
BUFFER = 4096
running = True
SHARED_SECRET = None

def clear():
    os.system("clear")

def show_logo():
    try:
        with open("logo.txt", "r") as f:
            print(f.read())
    except FileNotFoundError:
        print("[Logo file not found]")

def stop_all(sig, frame):
    print("\n[!] Stopping chat and Tor...")
    try:
        subprocess.call(["sudo", "systemctl", "stop", "tor"])
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, stop_all)

# ---------------- AUTH ----------------

def authenticate(conn, is_host):
    global SHARED_SECRET

    if is_host:
        SHARED_SECRET = input("Set shared secret: ").strip()
        conn.send(SHARED_SECRET.encode())
        response = conn.recv(16).decode()
        return response == "OK"
    else:
        SHARED_SECRET = input("Enter shared secret: ").strip()
        received = conn.recv(1024).decode()
        if received != SHARED_SECRET:
            conn.send(b"NO")
            return False
        conn.send(b"OK")
        return True

# ---------------- PROGRESS BAR ----------------

def progress_bar(done, total, start_time, prefix=""):
    elapsed = time.time() - start_time
    speed = done / elapsed if elapsed > 0 else 0
    remaining = total - done
    eta = int(remaining / speed) if speed > 0 else 0

    percent = int((done / total) * 100)
    bars = int(percent / 5)
    bar = "█" * bars + "░" * (20 - bars)

    print(
        f"\r{prefix} [{bar}] {percent}% | "
        f"{int(speed/1024)} KB/s | ETA {eta}s",
        end="",
        flush=True,
    )

# ---------------- RECEIVE ----------------

def receive(conn):
    while running:
        try:
            data = conn.recv(BUFFER)
            if not data:
                break

            if data.startswith(b"FILE|"):
                _, filename, filesize = data.decode().split("|")
                filesize = int(filesize)

                print(f"\n[Receiving file: {filename}]")
                received = 0
                start = time.time()

                with open(filename, "wb") as f:
                    while received < filesize:
                        chunk = conn.recv(BUFFER)
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                        progress_bar(received, filesize, start, "Receiving")

                print(f"\n[File saved as {filename}]\n> ", end="")
            else:
                print("\nFriend:", data.decode(), "\n> ", end="")

        except:
            break

# ---------------- SEND FILE ----------------

def send_file(conn, path):
    if not os.path.exists(path):
        print("[File not found]")
        return

    filesize = os.path.getsize(path)
    filename = os.path.basename(path)

    header = f"FILE|{filename}|{filesize}".encode()
    conn.send(header)

    sent = 0
    start = time.time()
    print(f"[Sending file: {filename}]")

    with open(path, "rb") as f:
        while chunk := f.read(BUFFER):
            conn.send(chunk)
            sent += len(chunk)
            progress_bar(sent, filesize, start, "Sending")

    print(f"\n[File sent: {filename}]")

# ---------------- CHAT ----------------

def chat(conn):
    threading.Thread(target=receive, args=(conn,), daemon=True).start()

    while running:
        try:
            msg = input("> ")

            if msg.startswith("/send "):
                filepath = msg.split(" ", 1)[1]
                send_file(conn, filepath)
            else:
                conn.send(msg.encode())

        except:
            break

# ---------------- HOST / CONNECT ----------------

def host():
    s = socket.socket()
    s.bind(("127.0.0.1", PORT))
    s.listen(1)
    print("[Waiting for connection...]")
    conn, _ = s.accept()

    if not authenticate(conn, is_host=True):
        print("[Authentication failed]")
        conn.close()
        return

    print("[Connected ^_^]")
    chat(conn)

def connect(onion):
    s = socket.socket()
    s.connect((onion, PORT))

    if not authenticate(s, is_host=False):
        print("[Authentication failed]")
        s.close()
        return

    print("[Connected ^_^]")
    chat(s)

# ---------------- MAIN ----------------

clear()
show_logo()
print()
mode = input("Host (h) or Connect (c)? ").strip().lower()

if mode == "h":
    host()
else:
    onion = input("Enter .onion address: ").strip()
    connect(onion)
