#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
python3 run_development.py
printf '\nPress Return to close this window...'
read -r reply
