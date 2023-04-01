#!/bin/sh

export SHELLY_HOST=${SHELLY_HOST}
export SHELLY_AUTH_KEY=${SHELLY_AUTH_KEY}
export SHELLY_IPS=${SHELLY_IPS}

python3 run.py