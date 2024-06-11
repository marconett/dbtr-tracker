# Diabotical Rogue Tracker

This tools is supposed to run at least hourly as a cron job. It checks if the game was updated and if so, downloads it and collects text content and (meta) data included in the game.
Those files are added to a repo here <INSERT_REPO_LINK> and every time the game gets updated, a new commit is created, making it possible to track changes to the game.

It's like the following repo, but for Diabotical Rogue and using Steam instead of EGS: https://github.com/derrod/dbtracker

Game files are collected in a subfolder `game_files`, where the git repo mentioned above exists.

I reuse some tools here that were already open sourced: https://github.com/marconett/diabotical-tools

## Running it

The steam pypi package needs a patch, see https://github.com/ValvePython/steam/pull/437

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
patch venv/lib/python3.11/site-packages/steam/client/cdn.py < patches/cdn_client.patch

cp .env.example .env

mkdir game_files
cd game_files
git init .
git remote add ... # add a remote
```

Others things to do:
- Setup `.env` with a steam account that owns the game and has no authenticator connected
- Setup a cron job that runs `main.py` hourly
- Setup ssh keys so that the push works without the user present
- The game is around 9 GB, so the server that runs this will need at least that amount of space