#!/bin/bash
# usage: run_repeats.sh <system> <adapter> <track> <split> <reps>
set -u
SYS=$1; ADAPTER=$2; TRACK=$3; SPLIT=$4; REPS=$5
cd /Users/david/tests/jev_testing/work/rag-routing-benchmark-v2/multiturn
GOLD="${SPLIT}_gold.jsonl"
for i in $(seq 1 "$REPS"); do
  R=/Users/david/tests/jev_testing/runs/$SYS/${SPLIT}_${TRACK}/rep$i
  rm -rf "$R"; mkdir -p "$R"
  # Tunnels died mid-run and silently turned whole repeats into connection-refused
  # failures scored as 0. Re-establish before each repeat.
  for LP in ${TUNNELS:-}; do
    nc -z 127.0.0.1 "${LP%%=*}" 2>/dev/null ||       ssh -f -N -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=15           -o ServerAliveCountMax=3 -L "${LP%%=*}:localhost:${LP##*=}" H200
  done
  ROUTING_RAW_DIR="$R/raw" python3 run_replay.py --adapter "$ADAPTER" \
      --split "$SPLIT" --track "$TRACK" --out "$R/predictions.jsonl" || { echo "rep$i replay failed"; continue; }
  python3 evaluate.py "$GOLD" "$R/predictions.jsonl" --out "$R/results.json" >/dev/null || echo "rep$i eval failed"
  echo "[$SYS/$TRACK/$SPLIT] rep$i done"
done
