#!/bin/bash
# Main orchestration script for HN digest (v2 with new storage)

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON="$DIR/venv/bin/python"

# Logging with timestamps
log_step() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

START_TIME=$(date +%s)

log_step "🦅 Starting digest generation"

log_step "📡 Fetching HN stories..."
FETCH_START=$(date +%s)
$PYTHON fetch_stories.py > stories_raw.json
FETCH_END=$(date +%s)
FETCH_DURATION=$((FETCH_END - FETCH_START))
log_step "✓ HN stories fetched in ${FETCH_DURATION}s"

# Fetch Substack if enabled in config
log_step "📰 Fetching Substack feeds..."
SUBSTACK_START=$(date +%s)
$PYTHON fetch_substack.py > substack_raw.json 2>/dev/null || echo "[]" > substack_raw.json
SUBSTACK_END=$(date +%s)
SUBSTACK_DURATION=$((SUBSTACK_END - SUBSTACK_START))
log_step "✓ Substack fetched in ${SUBSTACK_DURATION}s"

# Merge HN + Substack stories into a single JSON array
log_step "🔄 Merging stories..."
MERGE_START=$(date +%s)
$PYTHON -c "
import json
hn = json.load(open('stories_raw.json'))
ss = json.load(open('substack_raw.json'))
json.dump(hn + ss, open('all_stories.json', 'w'))
"
MERGE_END=$(date +%s)
MERGE_DURATION=$((MERGE_END - MERGE_START))
log_step "✓ Stories merged in ${MERGE_DURATION}s"

log_step "🎯 Processing and generating digest..."
PROCESS_START=$(date +%s)
$PYTHON process_digest.py all_stories.json > digest.txt
PROCESS_END=$(date +%s)
PROCESS_DURATION=$((PROCESS_END - PROCESS_START))
log_step "✓ Digest generated in ${PROCESS_DURATION}s"

log_step "📱 Digest ready!"
cat digest.txt

# Archive today's data
log_step "💾 Archiving results..."
ARCHIVE_START=$(date +%s)
DATE=$(date +%Y-%m-%d)
mkdir -p archive
mkdir -p knos-digest

# Save to both locations
cp stories_raw.json "archive/${DATE}_stories.json"
cp digest.txt "archive/${DATE}_digest.txt"
cp digest.txt "knos-digest/${DATE}.md"
ARCHIVE_END=$(date +%s)
ARCHIVE_DURATION=$((ARCHIVE_END - ARCHIVE_START))
log_step "✓ Archived in ${ARCHIVE_DURATION}s"

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

log_step "✅ Done! Total time: ${TOTAL_DURATION}s"
log_step "   Breakdown: Fetch=${FETCH_DURATION}s, Substack=${SUBSTACK_DURATION}s, Merge=${MERGE_DURATION}s, Process=${PROCESS_DURATION}s, Archive=${ARCHIVE_DURATION}s"
log_step "   Digest saved to:"
log_step "   - archive/${DATE}_digest.txt"
log_step "   - knos-digest/${DATE}.md"
