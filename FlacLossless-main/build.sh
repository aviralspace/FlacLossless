#!/usr/bin/env bash
# build.sh for Render deployment

set -o errexit

# Install system dependencies
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
pip install -r requirements.txt
