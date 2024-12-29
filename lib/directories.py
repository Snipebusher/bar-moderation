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
import pathlib
import traceback
from typing import NamedTuple, Union, Literal
from .replays import Header
from .teamcolors import setupTeamColors
from .replays import Replay, readReplay
from .pages import buildPage

def buildDirectoryPage(dir: str):
  dirobj = pathlib.Path(dir)

  subdirs = [subdir for subdir in dirobj.iterdir() if subdir.is_dir()]
  replayFiles = [file for file in dirobj.iterdir() if file.is_file() and file.suffix == ".sdfz"]

  def builSubDirs():
    if not subdirs: return ""

    return """
<div id="subdirs">
  <h3 class="collapser">Subdirectories [%s]</h3>
  <div class="collapsable">
%s
  </div>
</div>
""" % (
      "+" if replayFiles else "-",
      "".join("""
<span><a href="/view/%s">%s/</a></span>
""" % (
        str(subdir).removeprefix("/"),
        subdir.name,
      ) for subdir in subdirs))
  
  def buildReplays():
    if not replayFiles: return ""

    rows: list[str] = []
    for file in replayFiles:
      try:
        replay = readReplay(str(file), chunks=False)
        game = replay.setupScript["game"]

        duration = replay.header.wallclockTime
        hours, duration = divmod(duration, 3600)
        minutes, seconds = divmod(duration, 60)
        if hours: durationStr = "%dh%02dm%02ds" % (hours, minutes, seconds)
        elif minutes: durationStr = "%dm%02ds" % (minutes, seconds)
        else: durationStr = "%ds" % (seconds)

        def cssRgb(color):
          return "rgb(%f%%, %f%%, %f%%)" % tuple(100 * v for v in color)
        playerColors = setupTeamColors(game)
        teams: list[tuple[str, list[tuple[str, str]]]] = [("Team %d" % (teamid + 1), []) for teamid, _ in enumerate(game["allyteam"])]
        for playerid, player in enumerate(game["player"]):
          if player.get("team") is None: continue
          teams[game["team"][player["team"]]["allyteam"]][1].append(
            (cssRgb(playerColors[playerid]), html.escape(str(player["name"]))))
        ffaPlayers = []
        for _, players in teams:
          if len(players) == 1:
            ffaPlayers.append(players.pop())
        teams.append(("FFA", ffaPlayers))
        playersStr = "".join("""
            <div class="team">
              <span>%s:</span>
              <div class="players">%s</div>
            </div>
  """ % (name, "".join(("""
            <span class="player" style="border-color: %s">%s</span>
  """ % player for player in players))) for (name, players) in teams if players)

        rows.append("""
        <tr>
          <td>%s</td>
          <td><a href="/view/%s">%s</a></td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
        </tr>
  """ % (
          replay.header.unixTime.isoformat(" "),
          str(file).removeprefix("/"),
          replay.header.gameID,
          html.escape(str(game["mapname"])),
          durationStr,
          playersStr,
        ))
      except Exception as e:
        rows.append("""
      <tr><td colspan="5">Failed to parse replay: %s</td></tr>
""" % (str(file)))
        traceback.print_exception(e)

    return """
<div>
  <h3>Replays</h3>
  <table id="replays">
    <thead>
      <th>Time</th>
      <th>Game ID</th>
      <th>Map</th>
      <th>Duration</th>
      <th>Players</th>
    </thead>
    <tbody>%s</tbody>
  </table>
</div>
""" % ("".join(rows))
    
  content = "".join((builSubDirs(), buildReplays()))

  return buildPage(filename=dir, style=STYLE, content=content)

STYLE = """
#subdirs .collapsable {
  display: flex;
  flex-wrap: wrap;
}

#subdirs .collapsable > * {
  display: inline-block;
  min-width: 200px;
  margin: 5px;
  padding: 1px 7px;
  border: 1px solid lightGrey;
  border-radius: 5px;
}

#replays .team {
  display: flex;
  padding: 3px 2px;
  margin: 2px;
}

#replays .team > *:first-child {
  display: inline-block;
  min-width: 60px;
}

#replays .player {
  display: inline-block;
  background-color: white;
  border-width: 2px;
  border-left-width: 12px;
  border-style: solid;
  padding: 0 3px;
  margin: 1px 2px;
  border-radius: 4px;
}

#replays td {
  border-bottom: 2px solid lightGrey;
}

#replays td:nth-child(1) {
  min-width: 145px;
  text-align: center;
}

#replays td:nth-child(2) {
  min-width: 255px;
  text-align: center;
}

#replays td:nth-child(3) {
  min-width: 180px;
  text-align: center;
}

#replays td:nth-child(4) {
  min-width: 80px;
  text-align: right;
  padding-right: 10px;
}

#replays td:nth-child(5) {
  min-width: 500px;
}
"""
