#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "$(uname -s)" == "Darwin" ]]; then

  if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
  else
    echo "python3.13 est requis pour installer SupportX. Installez-le puis relancez ce script."
    exit 1
  fi

  if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
    "$PYTHON_BIN" -m venv "$SCRIPT_DIR/.venv"
  fi

  "$SCRIPT_DIR/.venv/bin/python" -m pip install --upgrade pip
  "$SCRIPT_DIR/.venv/bin/python" -m pip install -r "$SCRIPT_DIR/../config/requirements.txt"

  mkdir -p "$HOME/Desktop"
  ln -sfn "$SCRIPT_DIR/start-supportx.command" "$HOME/Desktop/SupportX.command"
  chmod +x "$HOME/Desktop/SupportX.command"

  mkdir -p "$HOME/Applications"
  ln -sfn "$SCRIPT_DIR/start-supportx.command" "$HOME/Applications/SupportX.command"
  chmod +x "$HOME/Applications/SupportX.command"

  echo "Installation terminée."
  echo "Lance l'application depuis SupportX.command sur le bureau."
  exit 0
fi

exec "$SCRIPT_DIR/install-supportx.sh"
