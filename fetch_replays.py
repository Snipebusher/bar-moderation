# this script uses the website's API to download replays

import requests
import os
import datetime
import urllib

API_URL = "https://api.bar-rts.com"

# dirtily exctracted from the website, no idea how long it will stay valid
STORAGE_AUTH = "AUTH_10286efc0d334efd917d476d7183232e"
STORAGE_URL = "https://storage.uk.cloud.ovh.net/v1/%s/BAR/demos/%s"

PARAMS = dict(limit=24, maps="All That Glitters v2.2")

replaysDirname = os.path.join(os.path.dirname(__file__), "replays")

utcnow = datetime.datetime.now(datetime.timezone.utc)
downloadUntil = utcnow - datetime.timedelta(days=2)
# for name in os.listdir(replaysDirname):
#   if not name.endswith(".sdfz"): continue
#   parts = name.split("_")
#   try: 
#     replayTime = datetime.datetime.strptime(
#       "%s_%s000" % (parts[0], parts[1]), "%Y-%m-%d_%H-%M-%S-%f")
#   except Exception as e:
#     print("couldn't parse filename datetime:", name, e)
#     continue
#   downloadUntil = max(downloadUntil, replayTime.astimezone(datetime.timezone.utc))

replayNames = []
listParams = dict(PARAMS, page=1)
listRes = requests.get("%s/replays" % (API_URL), params=listParams)
listRes.raise_for_status()
while len(listRes.json()["data"]):
  print("listing page", listParams["page"])
  for entry in listRes.json()["data"]:
    replayTime = datetime.datetime.fromisoformat(entry["startTime"])
    if replayTime <= downloadUntil: break
    if entry["durationMs"] <= 3 * 60 * 1000: continue # 3 minutes
    replayRes = requests.get("%s/replays/%s" % (API_URL, entry["id"]))
    replayRes.raise_for_status()
    replayName = replayRes.json()["fileName"]
    if os.path.isfile(os.path.join(replaysDirname, replayName)): continue
    replayNames.append(replayName)
  else:
    listParams["page"] += 1
    listRes = requests.get("%s/replays" % (API_URL), params=listParams)
    continue
  break

print("found", len(replayNames), "new replays")

if not os.path.exists(replaysDirname):
    os.makedirs(replaysDirname)

for replayName in reversed(replayNames):
  replayUrl = STORAGE_URL % (STORAGE_AUTH, urllib.parse.quote(replayName))
  print("downloading", replayUrl)
  target = os.path.join(replaysDirname, replayName)
  urllib.request.urlretrieve(replayUrl, target + ".tmp")
  os.rename(target + ".tmp", target)
