import socket
import threading
import time
import base64
import hashlib
import datetime
import json
import os
import getpass

HOST = "server4.beyondallreason.info"
PORT = 8200
CLIENT = "python tests"

def hash_password(password):
  return base64.b64encode(hashlib.md5(password.encode()).digest()).decode()

LOGIN = input("username:")
HASHED_PASSWORD = hash_password(getpass.getpass("password:"))

def read_lobbies(host, port, login, hashed_password, duration=10):
  lobbies = []

  conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  conn.connect((host, port))

  rest = b""

  def read():
    nonlocal rest
    if rest is None: return None
    while b"\n" not in rest:
      chunk = conn.recv(256)
      if not chunk:
        rest = None
        return None
      rest += chunk
    msg, rest = rest.split(b"\n", 1)
    return msg

  def send(data):
    if isinstance(data, str):
      data = data.encode()
    if data and data[-1] != b"\n":
      data += b"\n"
    conn.send(data)

  def listen():
    loggedin = False
    joined = False
    while True:
      msg = read()
      if not msg: break
      if b" " in msg:
        action, msg = msg.split(b" ", 1)
      else:
        action, msg = msg, b""
      action = action.decode()
      if not loggedin and action == "TASSERVER":
        print ("logging in")
        send("LOGIN %s %s 0 * %s	2797702286 6fd3679ffe4cbbce	b sp\n" % (login, hashed_password, CLIENT))
        loggedin = True
      if not joined and action == "ACCEPTED":
        print ("joining main")
        send(b"JOIN main\n")
        joined = True
      if action == "BATTLEOPENED":
        parts = msg.decode().split(" ", 10)
        if len(parts) != 11:
          raise Exception("incomplete BATTLEOPENED msg: %r" % (msg))
        battleID, type, natType, founder, ip, port, maxPlayers, passworded, rank, mapHash, other = parts
        battleID, type, natType, port, maxPlayers, passworded, rank, mapHash = int(battleID), int(type), int(natType), int(port), int(maxPlayers), int(passworded), int(rank), int(mapHash)
        parts = other.split("\t", 4)
        if len(parts) != 5:
          raise Exception("incomplete BATTLEOPENED msg.other: %r" % (msg))
        engine, engineVersion, mapName, lobbyName, client = parts
        print("new lobby:", founder, lobbyName)
        lobbies.append(dict(
          time=time.time(),
          battleID=battleID,
          founder=founder,
          ip=ip,
          port=port,
          maxPlayers=maxPlayers,
          passworded=passworded,
          rank=rank,
          mapHash=mapHash,
          mapName=mapName,
          lobbyName=lobbyName,
        ))

  thread = threading.Thread(target=listen, daemon=True)
  thread.start()

  time.sleep(duration)
  conn.shutdown(socket.SHUT_RDWR)

  thread.join()

  return lobbies

if not os.path.exists(os.path.join(os.path.dirname(__file__), "lobbies")):
    os.makedirs(os.path.join(os.path.dirname(__file__), "lobbies"))

lobbies = read_lobbies(HOST, PORT, LOGIN, HASHED_PASSWORD)

strnow = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")
lobbies_filename = os.path.join(
  os.path.relpath(os.path.dirname(__file__)),
  "lobbies",
  "lobbies-%s.json" % (strnow),
)

print ("saving lobbies:", lobbies_filename)
with open(lobbies_filename, "w+") as f:
  json.dump(lobbies, f, indent=2)
