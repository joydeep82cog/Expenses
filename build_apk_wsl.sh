#!/usr/bin/env bash
set -euo pipefail

# Run from project root (folder containing this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f buildozer.spec ]]; then
  echo "ERROR: buildozer.spec not found in $SCRIPT_DIR"
  exit 1
fi

sudo apt-get update
TINFO_PKG="libtinfo5"
if ! apt-cache show "$TINFO_PKG" >/dev/null 2>&1; then
  TINFO_PKG="libtinfo6"
fi

sudo apt-get install -y \
  git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
  libncursesw5-dev "$TINFO_PKG" cmake libffi-dev libssl-dev

python3 -m venv .venv-build
source .venv-build/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install "cython<3" buildozer

# Build debug APK
buildozer -v android debug

echo "Build finished. APK is in: $SCRIPT_DIR/bin"
