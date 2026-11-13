#!/bin/sh
# One review round: fold exported marks into overrides, regenerate, rebuild docs, refresh the review page data.
# Usage: tools/round.sh <marksDir> <bcsDir> <captureDir> <videoDir> <reviewOutDir>
set -e; cd "$(dirname "$0")/.."
python3 tools/apply_marks.py "$1"
python3 tools/process.py "$2" | tail -1
python3 tools/features.py | tail -1
python3 tools/apply_other.py
node tools/build.js "$3" "$4" | tail -1
ls "$5/s" > "$5/../old.txt"
python3 tools/review.py "$5"
