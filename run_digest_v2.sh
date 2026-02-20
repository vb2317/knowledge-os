#!/bin/bash
# Main orchestration script for HN digest (v2 with new storage)

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON=/usr/bin/python3

echo "🦅 Fetching HN stories..." >&2
$PYTHON fetch_stories.py > stories_raw.json

echo "🎯 Processing and generating digest..." >&2
$PYTHON process_digest.py stories_raw.json > digest.txt

echo "📱 Digest ready!" >&2
cat digest.txt

# Archive today's data
DATE=$(date +%Y-%m-%d)
mkdir -p archive
mkdir -p knos-digest

# Save to both locations
cp stories_raw.json "archive/${DATE}_stories.json"
cp digest.txt "archive/${DATE}_digest.txt"
cp digest.txt "knos-digest/${DATE}.md"

echo "✅ Done! Digest saved to:" >&2
echo "   - archive/${DATE}_digest.txt" >&2
echo "   - knos-digest/${DATE}.md" >&2
