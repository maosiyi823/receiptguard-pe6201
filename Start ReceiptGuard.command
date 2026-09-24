#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 first_ai_run.py
else
  echo 'Python 3 is not available. Ask for setup help; no request was sent.'
fi
printf '\nPress Return to close this window...'
read -r reply
