from __future__ import print_function

import steam.monkey
steam.monkey.patch_minimal()

import requests
import json
import os

from steam.client import SteamClient
from steam.client.cdn import CDNClient
from dotenv import load_dotenv

load_dotenv()

LOGON_DETAILS = {
  'username': os.getenv("STEAM_USERNAME"),
  'password': os.getenv("STEAM_PASSWORD"),
}

APP_ID = 2805060
DEPOT_ID = 2805061
OUT_PATH = "./game_files/"
BYTE_SIZE = 2048

###
### Steam login
###
def steam_login():
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

  return client

###
### Download files
###
def download_file(client, filter, manifest_gid=0):
  cdn_client = CDNClient(client)

  mrc = cdn_client.get_manifest_request_code(app_id=APP_ID, depot_id=DEPOT_ID, manifest_gid=manifest_gid)
  manifest = cdn_client.get_manifest(app_id=APP_ID, depot_id=DEPOT_ID, manifest_gid=manifest_gid, manifest_request_code=mrc)
  manifest_path = "./by_manifest/" + str(manifest_gid) + "/"

  for game_file in list(manifest.iter_files(filter)):
    try:
      if game_file.seekable:
        os.makedirs(manifest_path + os.path.dirname(game_file.filename), exist_ok=True)
        with open(manifest_path + game_file.filename, 'wb') as f:
          for i in range(int((game_file.size - (game_file.size % BYTE_SIZE)) / BYTE_SIZE)):
            f.write(game_file.read(BYTE_SIZE))
          f.write(game_file.read((game_file.size % BYTE_SIZE)))
    except Exception as e:
      print(f"An error occurred while processing {game_file.filename}: {e}")
      continue


###
### download all .exe file from each known manifest
###
if __name__ == "__main__":
  steam_client = steam_login()

  with open(OUT_PATH + "/manifests.json", 'r', encoding='utf-8') as f:
    for m in list(json.load(f)):
      download_file(steam_client, "diabotical.exe", m["manifest_gid"])

  steam_client.logout()