#!/bin/bash

cd ~/ramp-udp

export PYTHONPATH=src
export RAMP_LOCAL_HOST=10.0.0.1
export RAMP_LOCAL_PORT=6000
export RAMP_PEER_HOST=10.0.0.2
export RAMP_PEER_PORT=6001
export RAMP_AUTH_ENABLED=1


echo " RAMP-UDP Sender"

echo "Local : $RAMP_LOCAL_HOST:$RAMP_LOCAL_PORT"
echo "Peer  : $RAMP_PEER_HOST:$RAMP_PEER_PORT"
echo "Auth  : ENABLED"


python3 applications/chat_sender_app.py
