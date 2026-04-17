#!/bin/bash
# Generate HN digest and send with feedback buttons

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Generate digest
echo "[$(date '+%H:%M:%S')] Generating digest..." >&2
bash run_digest_v2.sh 2>&1 | tee /tmp/digest_log.txt >&2

# Check if digest was generated successfully
if [ ! -f "digest.txt" ]; then
    echo "Error: digest.txt not generated" >&2
    exit 1
fi

# Output digest text
cat digest.txt

# If metadata exists, output feedback card
if [ -f "digest_metadata.json" ]; then
    echo "" >&2
    echo "[$(date '+%H:%M:%S')] Preparing feedback card..." >&2
    
    # Generate feedback card
    PYTHON="${DIR}/venv/bin/python"
    STORY_COUNT=$(cat digest_metadata.json | $PYTHON -c "import json,sys; print(len(json.load(sys.stdin).get('stories', [])))")
    
    if [ "$STORY_COUNT" -gt 0 ]; then
        echo "" # Blank line separator
        echo "📊 *Rate Today's Stories*"
        echo ""
        echo "_Tap buttons to provide feedback (helps improve future digests):_"
        echo ""
        
        # Output button instructions for the agent
        echo "---"
        echo "FEEDBACK_BUTTONS_NEEDED: $STORY_COUNT stories"
        echo "Metadata: digest_metadata.json"
        echo ""
        echo "Instructions: Send a follow-up message with inline buttons for each story."
        echo "Button format: Story N - 👍 Like | 📌 Save | 👎 Skip"
        echo "Callback data: hn_like:{story_id}, hn_save:{story_id}, hn_skip:{story_id}"
    fi
fi

echo "" >&2
echo "[$(date '+%H:%M:%S')] Done!" >&2
