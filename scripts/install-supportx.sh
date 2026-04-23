#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"


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

mkdir -p "$HOME/.local/share/applications"

APP_DESKTOP_FILE="$HOME/.local/share/applications/supportx.desktop"
cat > "$APP_DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SupportX
Comment=SupportX App
Exec=$SCRIPT_DIR/start-supportx.sh
Icon=$SCRIPT_DIR/image/logo/logo-notification.ico
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

chmod +x "$APP_DESKTOP_FILE"

# Resolve desktop directory across locales (Desktop/Bureau/XDG config).
DESKTOP_DIR=""
if command -v xdg-user-dir >/dev/null 2>&1; then
  DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
fi

if [[ -z "$DESKTOP_DIR" || "$DESKTOP_DIR" == "$HOME" ]]; then
  if [[ -d "$HOME/Desktop" ]]; then
    DESKTOP_DIR="$HOME/Desktop"
  elif [[ -d "$HOME/Bureau" ]]; then
    DESKTOP_DIR="$HOME/Bureau"
  fi
fi

if [[ -n "$DESKTOP_DIR" && -d "$DESKTOP_DIR" ]]; then
  cp "$APP_DESKTOP_FILE" "$DESKTOP_DIR/SupportX.desktop"
  chmod +x "$DESKTOP_DIR/SupportX.desktop"
fi

echo "Installation terminée."
echo "Lance l'application avec le raccourci SupportX sur le bureau ou dans les applications."
