# This script reads all replays in `replays` folder and makes a summary in `build` folder

import socket
import threading
import time
import base64
import hashlib
import sys
import struct
import datetime
import re
import gzip
import json
import os
import html
from typing import NamedTuple, Union, Literal

REPLAY_PAGE = "https://www.beyondallreason.info/replays?gameId=%s"
MATCH_PAGE = "https://server4.beyondallreason.info/battle/%s"

# colors from replays aren't used, dirty fix
COLORS_8v8 = {
  5: "rgb(27, 112, 47)",
  6: "rgb(124, 194, 255)",
  4: "rgb(143, 255, 148)",
  7: "rgb(162, 148, 255)",
  1: "rgb(12, 233, 8)",
  2: "rgb(0, 245, 229)",
  3: "rgb(105, 65, 242)",
  0: "rgb(11, 62, 243)",
  10: "rgb(255, 97, 7)",
  8: "rgb(255, 16, 5)",
  14: "rgb(241, 144, 179)",
  9: "rgb(255, 210, 0)",
  15: "rgb(200, 139, 47)",
  12: "rgb(252, 238, 164)",
  13: "rgb(138, 40, 40)",
  11: "rgb(248, 0, 137)",
}

def loadLobbies():
  lobbies: dict[str, list[tuple[float, str]]] = {}
  dirname = os.path.join(os.path.dirname(__file__), "lobbies")
  for filename in os.listdir(dirname):
    filename = os.path.join(dirname, filename)
    if not filename.endswith(".json"): continue
    with open(filename, "r") as f:
      entries = json.load(f)
    for entry in entries:
      time: float = entry["time"]
      founder: str = entry["founder"]
      lobbyName: str = entry["lobbyName"]
      if founder not in lobbies: lobbies[founder] = []
      lobbies[founder].append((time, lobbyName))
  for entries in lobbies.values():
    entries.sort(key=lambda t: t[0])
  return lobbies

if not os.path.exists(os.path.join(os.path.dirname(__file__), "lobbies")):
  os.makedirs(os.path.join(os.path.dirname(__file__), "lobbies"))
LOBBIES = loadLobbies()

def parseScript(script: str):
  stack = [{}]
  tag = None
  tagIndex = None
  for l in script.split("\n"):
    l = l.strip()
    if not l: continue
    if l.startswith("["):
      m = re.match(r"^\[([a-zA-Z]+)([0-9]+)?\]$", l)
      if m:
        tag = m.group(1)
        tagIndex = int(m.group(2)) if m.group(2) else None
        continue
    elif l == "{":
      if tag is None:
        raise Exception("unexpected script line %r without tag declaration" % (l))
      elif tagIndex is None:
        if tag in stack[-1]:
          raise Exception("duplicate script tag %r" % (tag))
        params = {}
        stack[-1][tag] = params
        stack.append(params)
        continue
      else:
        if tag not in stack[-1]:
          stack[-1][tag] = []
        elif not isinstance(stack[-1][tag], list):
          raise Exception("tag %r is not a list" % (tag))
        while tagIndex > len(stack[-1][tag])-1:
          stack[-1][tag].append(None)
        if stack[-1][tag][tagIndex] is not None:
          raise Exception("duplicate script tag %r:%r" % (tag,tagIndex))
        params = {}
        stack[-1][tag][tagIndex] = params
        stack.append(params)
        continue
    elif l == "}":
      if len(stack) <= 1:
        raise Exception("unexpected script line %r without tag declaration" % (l))
      param = stack.pop(-1)
      for tag, array in param.items():
        if isinstance(array, list):
          for tagIndex, p in enumerate(array):
            if p is None:
              raise Exception("missing script tag %r:%r" % (tag,tagIndex))
      continue
    else:
      m = re.match(r"^(\w+)=(.*);$", l)
      if m:
        k = m.group(1)
        if k in stack[-1]:
          raise Exception("duplicate script field %r" % (k))
        v = m.group(2)
        if re.match(r"^[0-9]+$", v):
          v = int(v)
        elif re.match(r"^[0-9]+\.[0-9]+$", v):
          v = float(v)
        elif re.match(r"^[0-9]+\.[0-9]+ [0-9]+\.[0-9]+ [0-9]+\.[0-9]+$", v):
          v = tuple(float(f) for f in v.split(" "))
        stack[-1][k] = v
        continue
    raise Exception("unparsable script line %r" % (l))
  if len(stack) != 1:
    raise Exception("unexpected script end")
  param = stack.pop(-1)
  for tag, array in param.items():
    if isinstance(array, list):
      for tagIndex, p in enumerate(array):
        if p is None:
          raise Exception("missing script tag %r:%r" % (tag,tagIndex))
  return param

class Header(NamedTuple):
  version: int
  headerSize: int
  versionString: str
  gameID: str
  unixTime: datetime.datetime
  scriptSize: int
  demoStreamSize: int
  gameTime: int
  wallclockTime: int
  numPlayers: int
  playerStatSize: int
  playerStatElemSize: int
  numTeams: int
  teamStatSize: int
  teamStatElemSize: int
  teamStatPeriod: int
  winningAllyTeamsSize: int
  
def readReplay(filename: str):
  with gzip.open(filename, "rb") as f:
    def read_string(size: int):
      return f.read(size).split(b'\x00')[0].decode()

    def read_int() -> int:
      return struct.unpack("<i", f.read(4))[0]
    
    def read_ts():
      return datetime.datetime.fromtimestamp(struct.unpack("<Q", f.read(8))[0])

    magic = read_string(16)
    if magic != "spring demofile":
      raise Exception("not a spring demofile: %r" % (magic))
    
    version = read_int()
    headerSize = read_int()
    versionString = read_string(256)
    gameID = f.read(16).hex()
    unixTime = read_ts()
    scriptSize = read_int()
    demoStreamSize = read_int()
    gameTime = read_int()
    wallclockTime = read_int()
    numPlayers = read_int()
    playerStatSize = read_int()
    playerStatElemSize = read_int()
    numTeams = read_int()
    teamStatSize = read_int()
    teamStatElemSize = read_int()
    teamStatPeriod = read_int()
    winningAllyTeamsSize = read_int()

    rawSetupScript = read_string(scriptSize)
    setupScript = parseScript(rawSetupScript)

    chunks: list[tuple[float, bytes]] = []
    while True:
      header = f.read(8)
      if len(header) < 8: break
      gameTime: float = struct.unpack("<f", header[0:4])[0]
      length: int = struct.unpack("<I", header[4:8])[0]
      if length == 0: continue
      data = f.read(length)
      if len(data) < length: break
      chunks.append((gameTime, data))

  return (
    Header(
      version=version,
      headerSize=headerSize,
      versionString=versionString,
      gameID=gameID,
      unixTime=unixTime,
      scriptSize=scriptSize,
      demoStreamSize=demoStreamSize,
      gameTime=gameTime,
      wallclockTime=wallclockTime,
      numPlayers=numPlayers,
      playerStatSize=playerStatSize,
      playerStatElemSize=playerStatElemSize,
      numTeams=numTeams,
      teamStatSize=teamStatSize,
      teamStatElemSize=teamStatElemSize,
      teamStatPeriod=teamStatPeriod,
      winningAllyTeamsSize=winningAllyTeamsSize,
    ),
    rawSetupScript,
    setupScript,
    chunks,
  )

class Player(NamedTuple):
  index: int
  name: str
  spectator: int
  id: str = None
  rank: int = None
  skill: str = None
  skilluncertainty: float = None
  allyteam: int = None
  side: str = None
  rgbcolor: tuple[float, float, float] = None

LogLine = Union[
  tuple[float, int, int, Literal["JOINED"]],
  tuple[float, int, int, Literal["LEFT"], str],
  tuple[float, int, int, Literal["MSG"], str],
  tuple[float, int, int, Literal["PING"], str],
  tuple[float, int, int, Literal["PING"], tuple[Literal["PING"], list[float]]],
  tuple[float, int, int, Literal["DRAW"], tuple[Literal["DRAW"], list[tuple[float, int, int, int, int]]]],
]

class Replay(NamedTuple):
  filename: str
  header: Header
  rawScript: str
  game: dict
  players: dict[int, Player]
  startTime: float
  logLines: list[LogLine]
  lobbyName: tuple[str | None, str | None]

def decode(b: bytes):
  try: return b.decode()
  except: return b.decode("iso-8859-1")

def processReplay(filename: str):
  header, rawScript, setupScript, chunks = readReplay(filename)
  game = setupScript['game']

  teams = {
    i: dict(
      allyteam=team["allyteam"],
      side=team["side"],
      rgbcolor=team["rgbcolor"],
    ) for i, team in enumerate(game["team"])
  }

  players = {
    i: Player(
      index=i,
      id=player["accountid"],
      name=str(player["name"]),
      spectator=player["spectator"],
      rank=player.get("rank"),
      skill=player.get("skill"),
      skilluncertainty=player.get("skilluncertainty"),
      **(teams[player["team"]] if "team" in player else {}),
    ) for i, player in enumerate(game['player'])
  }

  startTime = 0
  playerCache = {} # a cache to sum up some consecutive actions
  logLines = []
  for gameTime, data in chunks:
    action = int(data[0])
    # game start event
    if action == 4: startTime = gameTime
    # new spectator joined event
    if action == 75:
      player = int(data[3])
      spectator = int(data[4])
      team = int(data[5])
      name = decode(data[6:])
      if player not in players:
        players[player] = Player(
          index=player,
          name=str(name),
          spectator=spectator,
        )
      logLines.append((gameTime, player, None, "JOINED", "Player joined"))
    # player left
    if action == 39:
      player = int(data[1])
      reason = {
        0: "Connection error",
        1: "Resigned" if not players[player].spectator else "Left",
        2: "Kicked",
      }.get(int(data[2]), "Unknown reason")
      logLines.append((gameTime, player, None, "LEFT", "Player left:" + reason))
    # chat message
    if action == 7:
      msgFrom = int(data[2])
      msgTo = int(data[3])
      msgStr = decode(data[4:-1])
      logLines.append((gameTime, msgFrom, msgTo, "MSG", msgStr))
      playerCache.pop(msgFrom, None)
    # map draw
    if action == 31:
      drawFrom = int(data[2])
      drawType = int(data[3])
      # map ping
      if drawType == 0:
        msgStr = decode(data[9:-1])
        cache = playerCache.pop(drawFrom, None)
        if msgStr:
          logLines.append((gameTime, drawFrom, None, "PING", msgStr))
        else:
          if cache and cache[0] == "PING" and cache[1][-1] > gameTime - 2:
            cache[1].append(gameTime)
          else:
            cache = ("PING", [gameTime])
            logLines.append((gameTime, drawFrom, None, "PING", cache))
          playerCache[drawFrom] = cache
      # map draw
      elif drawType == 2:
        x1: int = struct.unpack("<h", data[4:6])[0]
        z1: int = struct.unpack("<h", data[6:8])[0]
        x2: int = struct.unpack("<h", data[8:10])[0]
        z2: int = struct.unpack("<h", data[10:12])[0]
        cache = playerCache.pop(drawFrom, None)
        if cache and cache[0] == "DRAW" and cache[1][-1][0] > gameTime - 5:
          cache[1].append((gameTime, x1, z1, x2, z2))
        else:
          cache = ("DRAW", [(gameTime, x1, z1, x2, z2)])
          logLines.append((gameTime, drawFrom, None, "DRAW", cache))
        playerCache[drawFrom] = cache
  
  lobbyEntries = LOBBIES.get(game["autohostname"], [])
  lobbyNameBefore, lobbyNameAfter = None, None
  for time, name in lobbyEntries:
    if time <= header.unixTime.timestamp():
      lobbyNameBefore = name
    if time >= header.unixTime.timestamp():
      lobbyNameAfter = name
      break

  return Replay(
    filename=filename,
    header=header,
    rawScript=rawScript,
    game=game,
    players=players,
    startTime=startTime,
    logLines=logLines,
    lobbyName=(lobbyNameBefore, lobbyNameAfter)
  )

SPECIAL_PLAYER_INDICES = {
  252: "[Allies]",
  253: "[Spectators]",
  254: "[Everyone]",
  255: "[Host]",
}

def buildReplayPage(replay: Replay):
  def cssRgb(color):
    return "rgb(%f%%, %f%%, %f%%)" % tuple(100 * v for v in color)

  def cssPlayerColors():
#     # TODO those are not the colors actually used by the game
#     return "\n".join("""
# .player-%d {
#   --player-color: %s;
# }
# """ % (player.index, cssRgb(player.rgbcolor)) for player in replay.players.values() if player.rgbcolor)
    return "\n".join("""
.player-%d {
  --player-color: %s;
}
""" % item for item in COLORS_8v8.items())

  def htmlHeader():
    lobbyNameBefore, lobbyNameAfter = replay.lobbyName
    lobbyNameBefore = html.escape(lobbyNameBefore or "???")
    lobbyNameAfter = html.escape(lobbyNameAfter or "???")
    if lobbyNameBefore == lobbyNameAfter:
      lobbyName = lobbyNameBefore
    else:
      lobbyName = "%s ~~~ %s" % (lobbyNameBefore, lobbyNameAfter)
    return """
<div>
  <a href="./index.html">&lt; back</a>
  ---
  <a href="%s">replay</a>
  ---
  <a href="%s">match</a>
  ---
  <code>%s</code>
</div>
<h1>%s</h1>
<h2>%s - %s</h2>
""" % (
  REPLAY_PAGE % (replay.header.gameID),
  MATCH_PAGE % (replay.game["server_match_id"]),
  os.path.abspath(replay.filename),
  lobbyName,
  html.escape(replay.game["mapname"]),
  replay.header.unixTime.isoformat(),
)

  def htmlHeaders():
    return """
<script type="text/javascript">
function switchHeader(event) {
  const h3 = event.target
  const pre = document.getElementById("headers")
  if (pre.style.display === "none") {
    pre.style.display = "block"
    h3.textContent = h3.textContent.replace("[+]", "[-]")
  } else {
    pre.style.display = "none"
    h3.textContent = h3.textContent.replace("[-]", "[+]")
  }
}
</script>
<h3 onclick="switchHeader(event)">Headers [+]</h3>
<pre id="headers" style="display: none">
%s
</pre>
""" % (html.escape(json.dumps(dict(replay.header._asdict(), unixTime=replay.header.unixTime.isoformat()), indent=2)))

  def htmlScript():
    return """
<script type="text/javascript">
function switchScript(event) {
  const h3 = event.target
  const pre = document.getElementById("script")
  if (pre.style.display === "none") {
    pre.style.display = "block"
    h3.textContent = h3.textContent.replace("[+]", "[-]")
  } else {
    pre.style.display = "none"
    h3.textContent = h3.textContent.replace("[-]", "[+]")
  }
}
</script>
<h3 onclick="switchScript(event)">Script [+]</h3>
<pre id="script" style="display: none">
%s
</pre>
""" % (html.escape(replay.rawScript))

  def playerName(index: int):
    if index in replay.players:
      return html.escape(replay.players[index].name)
    elif index in SPECIAL_PLAYER_INDICES:
      return html.escape(SPECIAL_PLAYER_INDICES[index])
    else:
      return ""

  def htmlLogLines():
    tableLines = []
    lastFrom = None
    for gameTime, playerFrom, playerTo, lineType, msgStr in replay.logLines:
      seconds = gameTime - replay.startTime
      format = "%02d:%02d:%05.2f"
      if seconds < 0: format = "-%01d:%02d:%05.2f"
      seconds = abs(seconds)
      hours = seconds // 3600
      seconds -= hours * 3600
      minutes = seconds // 60
      seconds -= minutes * 60
      timeStr = format % (hours, minutes, seconds)
      classes = ["player-%d" % (playerFrom)]
      if lastFrom != playerFrom: classes.append("player-start")
      lastFrom = playerFrom
      playerFromName = playerName(playerFrom)
      playerToName = playerName(playerTo)
      if isinstance(msgStr, tuple):
        if msgStr[0] == "PING":
          msgStr = """<span style="font-size: %d%%">%d times</span>""" % (100 + 5 * (len(msgStr[1]) - 1), len(msgStr[1]))
        elif msgStr[0] == "DRAW":
          _, minx, minz, maxx, maxz = msgStr[1][0]
          svgLines = []
          for _, x1, z1, x2, z2 in msgStr[1]:
            minx = min(minx, x1, x2)
            maxx = max(maxx, x1, x2)
            minz = min(minz, z1, z2)
            maxz = max(maxz, z1, z2)
          medx = (maxx + minx) / 2
          medz = (maxz + minz) / 2
          medsize = max(maxx - minx, maxz - minz) / 2 + 10
          svgSize = 100
          strokSize = medsize / svgSize
          for _, x1, z1, x2, z2 in msgStr[1]:
            svgLines.append("""<path d="M%d %d L%d %d" style="stroke-width: %d" />""" % (x1, z1, x2, z2, strokSize))
          medx = (maxx + minx) / 2
          medz = (maxz + minz) / 2
          medsize = max(maxx - minx, maxz - minz) / 2 + 10
          msgStr = """
<svg width="%d" height="%d" viewBox="%f %f %f %f">
%s
</svg>
""" % (
            svgSize, svgSize, 
            medx - medsize, medz - medsize, 2*medsize, 2*medsize, 
            "\n".join(svgLines))
        else:
          msgStr = ""
      else: msgStr = html.escape(msgStr)
      tds = "".join("<td>%s</td>" % (v or "") for v in 
        (timeStr, playerFromName, playerToName, lineType, msgStr))
      tableLines.append("""<tr class="%s">%s</tr>""" % (" ".join(classes), tds))
    return "\n".join(tableLines)

  return """
<html>
  <head>
    <style>

#log-table {{
  --player-color: lightGrey;
  --border-width: 4px;

  border-spacing: 0;
}}

#log-table td {{
  border: 0px solid var(--player-color);
  padding: 2px 8px;
}}

#log-table td:first-child {{
  border-left-width: 20px;
}}

#log-table td:last-child {{
  border-right-width: var(--border-width);
}}

#log-table tr.player-start td {{
  border-top-width: var(--border-width);
}}

#log-table svg path {{
  fill: none;
  stroke: black;
}}

#log-table tr.player-255 {{
  opacity: 0.5;
}}

{playerColors}
    </style>
  </head>
  <body>
{header}

{headers}

{setupScript}

    <table id="log-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Player</th>
          <th>Send to</th>
          <th>Type</th>
          <th>Content</th>
        </tr>
      </thead>
      <tbody>
{logLines}
      </tbody>
    </table>
  </body>
</html>
""".format(
    playerColors=cssPlayerColors(),
    header=htmlHeader(),
    headers=htmlHeaders(),
    setupScript=htmlScript(),
    logLines=htmlLogLines(),
  )

class ReplaySummary(NamedTuple):
  header: Header
  game: dict
  lobbyName: tuple[str | None, str | None]
  htmlname: str

def buildIndexPage(replays: list[ReplaySummary]):
  def replayLine(replay: ReplaySummary):
    lobbyNameBefore, lobbyNameAfter = replay.lobbyName
    lobbyNameBefore = html.escape(lobbyNameBefore or "???")
    lobbyNameAfter = html.escape(lobbyNameAfter or "???")
    if lobbyNameBefore == lobbyNameAfter:
      lobbyName = lobbyNameBefore
    else:
      lobbyName = "%s ~~~ %s" % (lobbyNameBefore, lobbyNameAfter)
    return (
      replay.header.unixTime.isoformat(),
      '<a href="%s">%s</a>' % (REPLAY_PAGE % (replay.header.gameID), replay.header.gameID),
      html.escape(replay.game["mapname"]),
      '<a href="./%s">%s</a>' % (replay.htmlname, lobbyName),
    )
  
  tableLines = "\n".join('<tr>\n%s\n</tr>' % ("\n".join('<td>%s</td>' % (cell) for cell in replayLine(replay))) for replay in replays)
  
  return """
<html>
  <head>
    <style>
#game-table {{
  border-spacing: 0;
  white-space:nowrap;
}}

#game-table td {{
  border: 0px solid var(--player-color);
  padding: 2px 8px;
}}
    </style>
  </head>
  <body>
    <table id="game-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>GameID</th>
          <th>Map</th>
          <th>Lobby</th>
        </tr>
      </thead>
      <tbody>
{lines}
      </tbody>
    </table>
  </body>
</html>
""".format(lines=tableLines)

def buildAll():
  replays: list[ReplaySummary] = []
  dirname = os.path.relpath(os.path.join(os.path.dirname(__file__), "replays"))
  indexname = os.path.relpath(os.path.join(os.path.dirname(__file__), "build", "index.html"))
  for filename in sorted(os.listdir(dirname), reverse=True):
    if not filename.endswith(".sdfz"): continue
    replayname = os.path.join(dirname, filename)
    print("processing", replayname)
    replay = processReplay(replayname)
    htmlname = os.path.relpath(os.path.join(os.path.dirname(__file__), "build",
      filename.removesuffix(".sdfz") + ".html"))
    print("writing", htmlname)
    with open(htmlname, "w+") as f:
      f.write(buildReplayPage(replay))
    replays.append(ReplaySummary(
      header=replay.header,
      game=replay.game,
      lobbyName=replay.lobbyName,
      htmlname=filename.removesuffix(".sdfz") + ".html",
    ))
    if len(replays) % 10 == 0:
      print("writing", indexname)
      with open(indexname, "w+") as f:
        f.write(buildIndexPage(replays))
  print("writing", indexname)
  with open(indexname, "w+") as f:
    f.write(buildIndexPage(replays))

if not os.path.exists(os.path.join(os.path.dirname(__file__), "replays")):
    os.makedirs(os.path.join(os.path.dirname(__file__), "replays"))
if not os.path.exists(os.path.join(os.path.dirname(__file__), "build")):
    os.makedirs(os.path.join(os.path.dirname(__file__), "build"))

buildAll()
