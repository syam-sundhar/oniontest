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

def stop_all(sig, frame):
    print("\n[!] Stopping chat and Tor...")
    try:
        subprocess.call(["sudo", "systemctl", "stop", "tor"])
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, stop_all)

def progress_bar(done, total, prefix=""):
    percent = int((done / total) * 100)
    bars = int(percent / 5)
    bar = "█" * bars + "░" * (20 - bars)
    print(f"\r{prefix} [{bar}] {percent}%", end="", flush=True)

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

                with open(filename, "wb") as f:
                    while received < filesize:
                        chunk = conn.recv(BUFFER)
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                        progress_bar(received, filesize, "Receiving")

                print(f"\n[File saved as {filename}]\n> ", end="")
            else:
                print("\nFriend:", data.decode(), "\n> ", end="")

        except:
            break

def send_file(conn, path):
    if not os.path.exists(path):
        print("[File not found]")
        return

    filesize = os.path.getsize(path)
    filename = os.path.basename(path)

    header = f"FILE|{filename}|{filesize}".encode()
    conn.send(header)

    sent = 0
    print(f"[Sending file: {filename}]")

    with open(path, "rb") as f:
        while chunk := f.read(BUFFER):
            conn.send(chunk)
            sent += len(chunk)
            progress_bar(sent, filesize, "Sending")

    print(f"\n[File sent: {filename}]")

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

def host():
    s = socket.socket()
    s.bind(("127.0.0.1", PORT))
    s.listen(1)
    print("[Waiting for connection...]")
    conn, _ = s.accept()
    print("[Connected]")
    chat(conn)

def connect(onion):
    s = socket.socket()
    s.connect((onion, PORT))
    print("[Connected]")
    chat(s)

mode = input("Host (h) or Connect (c)? ")

if mode.lower() == "h":
    host()
else:
    onion = input("Enter .onion address: ")
    connect(onion)
