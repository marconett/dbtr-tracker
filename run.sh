#!/bin/bash

source venv/bin/activate

if [ -z "$SSH_AUTH_SOCK" ] ; then
  eval `ssh-agent -s`
  ssh-add ~/.ssh/id_rsa_db
fi

python3 main.py

kill $SSH_AGENT_PID