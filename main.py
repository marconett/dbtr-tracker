from __future__ import print_function

import steam.monkey
steam.monkey.patch_minimal()

import requests
import json
import datetime
import os
import io
import subprocess
import shutil

from sys import platform
from steam.client import SteamClient
from steam.client.cdn import CDNClient
from pprint import pprint
from dotenv import load_dotenv
from pathlib import Path, PureWindowsPath

from dbp_packer import DBPReader
from skill_parser import create_asset_json as create_skill_json
from weapon_parser import create_asset_json as create_weapon_json

load_dotenv()

LOGON_DETAILS = {
    'username': os.getenv("STEAM_USERNAME"),
    'password': os.getenv("STEAM_PASSWORD"),
}

APP_ID = 2805060
OUT_PATH = "./game_files/"
BYTE_SIZE = 2048
LOCKFILE = '/tmp/dbtr-tracker.lock'

###
### Create lock
###
if os.path.exists(LOCKFILE):
  print("Another instance is already running.")
  exit(1)
else:
  with open(LOCKFILE, 'w') as lockfile:
    lockfile.write(str(os.getpid()))

###
### Steam login
###
client = SteamClient()

@client.on('error')
def error(result):
    print("Logon result:", repr(result))

@client.on('auth_code_required')
def auth_code_prompt(is_2fa, mismatch):
    print("this account has 2fa enabled")

try:
    client.login(**LOGON_DETAILS)
except:
    raise SystemExit

# print("-"*20)
# print("Logged on as:", client.user.name)
# print("Community profile:", client.steam_id.community_url)
# print("Last logon:", client.user.last_logon)
# print("Last logoff:", client.user.last_logoff)

###
### Collect data
###
cdnClient = CDNClient(client)
latest_manifest = cdnClient.get_manifests(APP_ID)[0]
time_obj = datetime.datetime.fromtimestamp(latest_manifest.creation_time)
time_string = time_obj.strftime('%Y-%m-%d %H:%M:%S') + " GMT+1"

###
### Check for new Manifest
###
manifest_file = OUT_PATH + '/manifests.json'

if not os.path.isfile(manifest_file):
  with open(manifest_file, 'w') as f:
    f.write('[]')

with open(manifest_file, 'r+', encoding='utf-8') as f:
  manifest_db = json.load(f)

  if (len(manifest_db) > 0 and manifest_db[0]['manifest_gid'] == latest_manifest.gid):
    print('no new manifest found')
    exit()

  new_item = {
    'app_id': latest_manifest.app_id,
    'depot_id': latest_manifest.depot_id,
    'manifest_gid': latest_manifest.gid,
    'creation_time': time_string
  }

  f.seek(0)
  json.dump([new_item] + manifest_db, f, ensure_ascii=False, indent=4)
  f.truncate()

###
### Write list of files
###
with open(OUT_PATH + "/files.txt", "w", encoding="utf-8") as f:
  for game_file in list(latest_manifest.iter_files()):
    sha1 = game_file.file_mapping.sha_content.hex()
    f.write(sha1 + "\t" + game_file.filename + "\t" + str(game_file.size) + "\n")

###
### Download the game
###
shutil.rmtree(OUT_PATH + "game/", ignore_errors=True)
os.mkdir(OUT_PATH + "game/")

for game_file in list(latest_manifest.iter_files()):
  if game_file.seekable:
    os.makedirs(OUT_PATH + "game/" + os.path.dirname(game_file.filename), exist_ok=True)
    with open(OUT_PATH + "game/" + game_file.filename, 'wb') as f:
      for i in range(int((game_file.size - (game_file.size % BYTE_SIZE)) / BYTE_SIZE)):
        f.write(game_file.read(BYTE_SIZE))
      f.write(game_file.read((game_file.size % BYTE_SIZE)))

###
### Steam logout
###
client.logout()

###
### Log the content of .dbp files
###
os.makedirs(OUT_PATH + "packs/", exist_ok=True)

for file_name in os.listdir(OUT_PATH + "game/packs/"):
  if file_name.endswith(".dbp"):
    f_in = io.open(OUT_PATH + "game/packs/" + file_name, 'rb')
    d = DBPReader.read(f_in)

    with open(OUT_PATH + "packs/" + file_name + ".files", "w", encoding="utf-8") as f:
      for df in d.index:
        f.write(f"{df.name}\t{df.size}\n")

###
### Unpack assets_shared.dbp
###
path_prefix = Path(PureWindowsPath(OUT_PATH))
os.makedirs(path_prefix, exist_ok=True)

f_in = io.open(OUT_PATH + "game/packs/assets_shared.dbp", 'rb')
d = DBPReader.read(f_in)

for df in d.index:
    path = Path(PureWindowsPath(df.name))
    full_path = path_prefix.joinpath(path)
    print(f"{path}\t{df.offset:08x}\t{df.size}")

    os.makedirs(full_path.parents[0], exist_ok=True)
    io.open(full_path, "wb").write(d.read_file(df))

###
### Output skills and weapons as JSON
###
parsed_path = OUT_PATH + "parsed/"
assets_path = OUT_PATH + "assets/"
os.makedirs(parsed_path, exist_ok=True)
create_skill_json(assets_path, parsed_path)
create_weapon_json(assets_path, parsed_path)

###
### Unpack UI
###
if platform == "linux":
    command = "./uiexporter-linux"
elif platform == "darwin":
    command = "./uiexporter-mac"
process = subprocess.Popen(command, shell=True)
process.wait()

###
### diabotical.exe strings
###
subprocess.run(f'strings -n 5 "{OUT_PATH}game/diabotical.exe" > "{OUT_PATH}diabotical.exe.strings"', shell=True, check=True)

###
### Release lock
###
if os.path.exists(LOCKFILE):
  os.remove(LOCKFILE)

###
### Git repo stuff
###
subprocess.run("git add .", shell=True, check=True, cwd=OUT_PATH)
subprocess.run(f"git commit -m '{str(latest_manifest.gid)}'", shell=True, check=True, cwd=OUT_PATH)
subprocess.run("git push --set-upstream origin main", shell=True, check=True, cwd=OUT_PATH)
