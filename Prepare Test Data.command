#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
python3 prepare_independent.py
printf '\nPress Return to close this window...'
read -r reply
