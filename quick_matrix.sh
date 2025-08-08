#!/usr/bin/env bash
set -e
declare -A cmds=(
  [ls]="/bin/ls /"
  [http]="wget -qO- http://example.com"
  [fork]="busybox sh -c 'sleep 0.1 & wait'"
)
for k in "${!cmds[@]}"; do
  echo -e "\n=== Scenario: $k ==="
  python -m autoseccomp.cli trace-run "${cmds[$k]}" -o "$k.json"
done
