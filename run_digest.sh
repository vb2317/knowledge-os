#!/bin/bash
# Main orchestration script for HN digest

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON=/usr/bin/python3

echo "🦅 Fetching HN stories..."
$PYTHON fetch_stories.py > stories_raw.json

echo "🎯 Matching topics..."
$PYTHON match_topics.py stories_raw.json > stories_matched.json

echo "📊 Tracking patterns..."
$PYTHON track_stories.py stories_matched.json > insights.json

echo "✍️  Generating digest..."
$PYTHON generate_digest.py stories_matched.json insights.json > digest.txt

echo "📱 Sending to WhatsApp..."
cat digest.txt

# Archive today's data
DATE=$(date +%Y-%m-%d)
mkdir -p archive
cp stories_matched.json "archive/${DATE}_stories.json"
cp insights.json "archive/${DATE}_insights.json"
cp digest.txt "archive/${DATE}_digest.txt"

echo "✅ Done! Digest saved to archive/${DATE}_digest.txt"
