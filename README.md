# Diabotical Rogue Tracker

This tools is supposed to run at least hourly as a cron job. It checks if the game was updated and if so, downloads it and collects text content and (meta) data included in the game.
Those files are added to a repo here https://github.com/marconett/diabotical-rogue-release-tracker and every time the game gets updated, a new commit is created, making it possible to track changes to the game.

It's like the following repo, but for Diabotical Rogue and using Steam instead of EGS: https://github.com/derrod/dbtracker

Game files are collected in a subfolder `game_files`, where the git repo mentioned above exists.

I reuse some tools here that were already open sourced: https://github.com/marconett/diabotical-tools

## Running it

The steam pypi package needs a patch, see https://github.com/ValvePython/steam/pull/437

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
patch venv/lib/python3.*/site-packages/steam/client/cdn.py < patches/cdn_client.patch

cp .env.example .env

mkdir game_files
cp game_files.gitignore game_files/.gitignore
cp README_release-tracker.md game_files/README.md

cd game_files
git init
git config commit.gpgsign false
git symbolic-ref HEAD refs/heads/main
git remote add origin git@github.com:marconett/diabotical-rogue-release-tracker.git # need write access
git add .gitignore README.md
git commit -m 'init'
git push --set-upstream origin main
```

Others things to do:
- Setup `.env` with a steam account that owns the game and has no authenticator connected
- Setup a cron job that runs `run.sh` hourly
- Setup write access ssh keys for the release-tracker repo
- The game is around 9 GB, so the server running this will need at least that amount of space