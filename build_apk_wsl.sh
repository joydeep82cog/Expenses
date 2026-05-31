#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
  zlib1g-dev libncurses5-dev libffi-dev libssl-dev

python3 -m pip install --upgrade pip
python3 -m pip install --user buildozer cython==0.29.37

export PATH="$HOME/.local/bin:$PATH"
buildozer -v android debug

echo "APK generated under ./bin/"
