#!/bin/bash

cd ~/ramp-udp

export PYTHONPATH=src
export RAMP_BIND_HOST=10.0.0.2
export RAMP_PORT=6001
export RAMP_AUTH_ENABLED=1


echo " RAMP-UDP Receiver"

echo "Listening : $RAMP_BIND_HOST:$RAMP_PORT"
echo "Auth      : ENABLED"


python3 applications/chat_receiver_app.py
