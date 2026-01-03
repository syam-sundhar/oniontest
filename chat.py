import socket
import threading
import signal
import subprocess
import sys
import os

PORT = 5555
running = True
prompt = "> "

# ===== Clear screen =====
def clear():
    os.system("clear")

# ===== Stop handler =====
def stop_all(sig, frame):
    global running
    print("\n[!] Stopping chat and Tor...")
    subprocess.call(["sudo", "systemctl", "stop", "tor"])
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, stop_all)

# ===== Receive messages =====
def receive(conn):
    while running:
        try:
            data = conn.recv(1024)
            if not data:
                break

            # Clear current input line and reprint prompt
            sys.stdout.write("\r")
            sys.stdout.write(" " * 80)
            sys.stdout.write("\r")

            print(f"Friend: {data.decode().strip()}")
            sys.stdout.write(prompt)
            sys.stdout.flush()

        except:
            break

# ===== Chat loop =====
def chat(conn):
    threading.Thread(target=receive, args=(conn,), daemon=True).start()
    while running:
        try:
            msg = input(prompt)
            conn.send(msg.encode())
        except:
            break

# ===== Host mode =====
def host():
    clear()
    s = socket.socket()
    s.bind(("127.0.0.1", PORT))
    s.listen(1)
    print("[Waiting for connection...]")
    conn, _ = s.accept()
    clear()
    print("[Connected]")
    chat(conn)

# ===== Connect mode =====
def connect(onion):
    clear()
    s = socket.socket()
    s.connect((onion, PORT))
    clear()
    print("[Connected]")
    chat(s)

# ===== Main =====
clear()
mode = input("Host (h) or Connect (c)? ").lower()

if mode == "h":
    host()
else:
    onion = input("Enter .onion address: ")
    connect(onion)
