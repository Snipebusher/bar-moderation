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
from collections import defaultdict
from .replays import Header, Replay, readReplay
from .teamcolors import setupTeamColors
from .pages import buildPage, THEME

REPLAY_PAGE = "https://www.beyondallreason.info/replays?gameId=%s"
MATCH_PAGE = "https://server4.beyondallreason.info/battle/%s"

class Player(NamedTuple):
  index: int
  name: str
  spectator: int = 1
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
  tuple[float, int, int, Literal["PAUSE"], str],
  tuple[float, int, int, Literal["PING"], str],
  tuple[float, int, int, Literal["PING"], tuple[Literal["PING"], list[float]]],
  tuple[float, int, int, Literal["DRAW"], tuple[Literal["DRAW"], list[tuple[float, int, int, int, int]]]],
]

class Summary(NamedTuple):
  header: Header
  rawScript: str
  game: dict
  players: dict[int, Player]
  startTime: float
  logLines: list[LogLine]
  # lobbyName: tuple[str | None, str | None]

def decode(b: bytes):
  try: return b.decode()
  except: return b.decode("iso-8859-1")

def processReplay(replay: Replay):
  game = replay.setupScript['game']

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
      id=player.get("accountid"),
      name=str(player["name"]),
      spectator=player.get("spectator"),
      rank=player.get("rank"),
      skill=player.get("skill"),
      skilluncertainty=player.get("skilluncertainty"),
      **(teams[player["team"]] if "team" in player else {}),
    ) for i, player in enumerate(game['player'])
  }

  startTime = 0
  playerCache = {} # a cache to sum up some consecutive actions
  logLines = []
  for gameTime, data in replay.chunks:
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
    # game pause/unpause
    if action == 13:
      player_index = int(data[1])
      mode = int(data[2])
      player_name = players[player_index].name if player_index in players else "Unknown Player"
      if mode == 1:
        logLines.append((gameTime, 255, None, "PAUSE", player_name + " paused the game"))
      else:
        logLines.append((gameTime, 255, None, "PAUSE", player_name + " unpaused the game"))
    # map draw
    if action == 31:
      drawFrom = int(data[2])
      drawType = int(data[3])
      # map ping
      if drawType == 0:
        msgStr = decode(data[9:-1])
        cache = playerCache.pop(drawFrom, None)
        if msgStr:
          logLines.append((gameTime, drawFrom, 252, "PING", msgStr))
        else:
          if cache and cache[0] == "PING" and cache[1][-1] > gameTime - 2:
            cache[1].append(gameTime)
          else:
            cache = ("PING", [gameTime])
            logLines.append((gameTime, drawFrom, 252, "PING", cache))
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
          logLines.append((gameTime, drawFrom, 252, "DRAW", cache))
        playerCache[drawFrom] = cache
  
  # lobbyEntries = LOBBIES.get(game["autohostname"], [])
  # lobbyNameBefore, lobbyNameAfter = None, None
  # for time, name in lobbyEntries:
  #   if time <= header.unixTime.timestamp():
  #     lobbyNameBefore = name
  #   if time >= header.unixTime.timestamp():
  #     lobbyNameAfter = name
  #     break

  return Summary(
    header=replay.header,
    rawScript=replay.rawSetupScript,
    game=game,
    players=players,
    startTime=startTime,
    logLines=logLines,
    # lobbyName=(lobbyNameBefore, lobbyNameAfter)
  )

SPECIAL_PLAYER_INDICES = {
  252: "[Allies]",
  253: "[Spectators]",
  254: "[Everyone]",
  255: "[Host]",
}

def buildReplayPage(filename: str):
  replay = readReplay(filename, chunks=True)
  summary = processReplay(replay)

  def cssRgb(color):
    return "rgb(%f%%, %f%%, %f%%)" % tuple(100 * v for v in color)

  def cssPlayerColors():
    return "".join("""
.player-%d {
  --player-color: %s;
}
""" % (playerid, cssRgb(playercolor)) for (playerid, playercolor) in setupTeamColors(summary.game).items())

  def htmlHeader():
    # lobbyNameBefore, lobbyNameAfter = summary.lobbyName
    # lobbyNameBefore = html.escape(lobbyNameBefore or "???")
    # lobbyNameAfter = html.escape(lobbyNameAfter or "???")
    # if lobbyNameBefore == lobbyNameAfter:
    #   lobbyName = lobbyNameBefore
    # else:
    #   lobbyName = "%s ~~~ %s" % (lobbyNameBefore, lobbyNameAfter)
    return """
<h1>%s - %s (<a href="%s">replay</a> / <a href="%s">match</a>)</h1>
""" % (
  summary.header.unixTime.isoformat(" "),
  html.escape(str(summary.game["mapname"])),
  REPLAY_PAGE % (summary.header.gameID),
  MATCH_PAGE % (summary.game["server_match_id"]) if summary.game.get("server_match_id") else "",
)

  def htmlHeaders():
    return """
<div id="headers">
  <h3 class="collapser">Headers [+]</h3>
  <pre class="collapsable">
%s
  </pre>
</div>
""" % (html.escape(json.dumps(dict(summary.header._asdict(), unixTime=summary.header.unixTime.isoformat()), indent=2)))

  def htmlScript():
    return """
<div id="script">
  <h3 class="collapser">Script [+]</h3>
  <pre class="collapsable">
%s
  </pre>
</div>
""" % (html.escape(summary.rawScript))

  def playerName(index: int):
    if index in summary.players:
      return html.escape(summary.players[index].name)
    elif index in SPECIAL_PLAYER_INDICES:
      return html.escape(SPECIAL_PLAYER_INDICES[index])
    else:
      return ""

  def htmlLogLines():
    tableLines: list[str] = []
    lastFrom = None
    for gameTime, playerFrom, playerTo, lineType, msgStr in summary.logLines:
      seconds = gameTime - summary.startTime
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
            svgLines.append("""
              <path d="M%d %d L%d %d" style="stroke-width: %d" />
""" % (x1, z1, x2, z2, strokSize))
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
            "".join(svgLines))
        else:
          msgStr = ""
      else: msgStr = html.escape(msgStr)
      tds = "".join("""
        <td>%s</td>
""" % (v or "") for v in 
        (timeStr, playerFromName, playerToName, lineType, msgStr))
      tableLines.append("""
      <tr class="%s">%s</tr>
""" % (" ".join(classes), tds))
      
    checkboxesLines: list[str] = []
    playersByTeam: dict[tuple[int, str, str], list[Player]] = defaultdict(list)
    playerIds: list[int] = [255]
    for player in summary.players.values():
      playerIds.append(player.index)
      if player.allyteam is None:
        playersByTeam[(200, "spectators", "[Spectators]")].append(player)
      else:
        playersByTeam[(
          player.allyteam,
          "team-%d" % (player.allyteam),
          "[Team %d]" % (player.allyteam + 1),
        )].append(player)
    for key, players in list(playersByTeam.items()):
      if 0 <= key[0] < 100 and len(players) == 1:
        playersByTeam[(100, "ffa", "[FFA]")].append(players.pop())
    playersByTeam[(-100, "host", "[Host]")].append(Player(
      index=255,
      name="[Host]"
    ))
    
    for key in sorted(playersByTeam):
      players = playersByTeam[key]
      if not players: continue
      _, cls, name = key

      checkboxesLines.append("""
    <div class="filter-team">
      <label class="filter-{cls}">
        <input type="checkbox" value="filter-{cls}" checked />
        <span>{name}:</span>
      </label>
      <div class="filter-players">
{children}
      </div>
    </div>
""".format(cls=cls, name=name, children="".join("""
        <label class="player-{playerid} filter-player filter-player-{playerid}">
          <input type="checkbox" class="parent-filter-{cls}" value="filter-player-{playerid}" checked />
          <span>{playername}</span>
        </label>
""".format(cls=cls, playerid=player.index, playername=html.escape(player.name)) for player in players)))
    
    filtersStyles: list[str] = []
    
    for playerid in playerIds:
      filtersStyles.append("""
#log-table.deselected-filter-player-{playerid} tr.player-{playerid} {{
  display: none !important;
}}

#log-table.deselected-filter-player-{playerid} label.filter-player-{playerid} {{
  opacity: 0.3;
}}
""".format(playerid=playerid))
      
    for key in sorted(playersByTeam):
      players = playersByTeam[key]
      if not players: continue
      _, cls, _ = key
      filtersStyles.append("""
#log-table.deselected-filter-{cls} label.filter-{cls} {{
  text-decoration: line-through;
}}

#log-table.partially-selected-filter-{cls} label.filter-{cls} {{
  font-style: italic;
}}
""".format(cls=cls))
    
    return "".join(filtersStyles), """
<div id="log-table">
  <h3>Logs</h3>
  <div class="filters">
    <h3 class="collapser">Filters [+]</h3>
    <div class="collapsable">
%s
    </div>
  </div>
  <table>
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
%s
    </tbody>
  </table>
</div>
""" % ("".join(checkboxesLines), "".join(tableLines))

  logStye, logContent = htmlLogLines()
  style = "".join((STYLE, logStye, cssPlayerColors()))
  content = """
%s

<div class="flex-container">
%s
%s
</div>

%s
""" % (htmlHeader(), htmlHeaders(), htmlScript(), logContent)

  return buildPage(filename=filename, style=style, content=content)

STYLE = """
.flex-container {
  display: flex;
}

.flex-container > * {
  width: 50%;
  flex: 1 1;
}

h1 {
  margin-left: 10;
}

h3 {
  margin-left: 10;
  cursor: pointer;
}

#log-table {
  --player-color: lightGrey;
  --border-width: 4px;

  position: relative
}

#log-table h3 {
  cursor: default;
}

#log-table .filters {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: white;
  border-radius: 5px;
}

#log-table .filters .collapser {
  float: right;
  margin: 0;
  padding: 5px;
  background-color: var(--collapser-bg) !important;
  color: var(--text-color);
  cursor: pointer;
}

#log-table .filters.collapsed .collapser {
  background-color: white;
}

#log-table .filters .collapsable {
  border: 2px solid lightGrey;
  border-radius: 10px;
}

label {
  cursor: pointer
}

#log-table .filters input[type=checkbox] {
  display: none;
}

#log-table .filters .filter-team {
  display: flex;
  // border-radius: 5px;
  // border: 2px solid lightGrey;
  padding: 3px 2px;
  margin: 2px;
}

#log-table .filters .filter-team > label {
  display: inline-block;
  min-width: 80px;
}

#log-table .filters .filter-players {
  display: inline-block;
  margin-left: 15px;
}

#log-table .filters .filter-player {
  display: inline-block;
  background-color: var(--filter-player-bg);
  border-color: var(--player-color);
  border-width: 2px;
  border-left-width: 12px;
  border-style: solid;
  padding: 0 3px;
  margin: 1px 2px;
  border-radius: 4px;
}

#log-table table {
  border-spacing: 0;
  clear: both;
}

#log-table td {
  border: 0px solid var(--player-color);
  padding: 2px 8px;
}

#log-table td:first-child {
  border-left-width: 20px;
}

#log-table td:last-child {
  border-right-width: var(--border-width);
}

#log-table tr.player-start td {
  border-top-width: var(--border-width);
}

#log-table svg path {
  fill: none;
  stroke: var(--draw-color);
}

#log-table tr.player-255 {
  opacity: 0.5;
}

#log-table td:nth-child(2), #log-table td:nth-child(3) {
  min-width: 80px;
}

#log-table td:nth-child(4) {
  min-width: 55px;
}

#log-table td:nth-child(5) {
  min-width: 500px;
}
"""
