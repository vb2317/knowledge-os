#!/usr/bin/env python3
"""
Send HN digest with feedback buttons
Outputs: digest text + feedback card with inline buttons
"""
import json
import sys
from pathlib import Path

def load_digest_metadata():
    """Load story metadata from the digest generation"""
    metadata_path = Path(__file__).parent / "digest_metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            return json.load(f)
    return {"stories": []}

def generate_feedback_card(stories):
    """Generate feedback button message"""
    if not stories:
        return None
    
    lines = ["📊 *Rate Today's Stories*", ""]
    
    for idx, story in enumerate(stories[:10], 1):  # Max 10 stories
        title = story['title'][:60] + "..." if len(story['title']) > 60 else story['title']
        lines.append(f"{idx}. {title}")
    
    lines.append("")
    lines.append("_Tap buttons below to give feedback:_")
    
    # Generate buttons JSON for OpenClaw message tool
    # Format: [[{text, callback_data, style}]]
    buttons = []
    for idx, story in enumerate(stories[:10], 1):
        story_id = story.get('id', f"story_{idx}")
        row = [
            {"text": f"{idx} 👍", "callback_data": f"hn_like:{story_id}"},
            {"text": f"{idx} 📌", "callback_data": f"hn_save:{story_id}"},
            {"text": f"{idx} 👎", "callback_data": f"hn_skip:{story_id}"}
        ]
        buttons.append(row)
    
    return {
        "text": "\n".join(lines),
        "buttons": buttons
    }

def main():
    # Read digest text
    digest_path = Path(__file__).parent / "digest.txt"
    if not digest_path.exists():
        print("Error: digest.txt not found", file=sys.stderr)
        sys.exit(1)
    
    with open(digest_path) as f:
        digest_text = f.read()
    
    # Load story metadata
    metadata = load_digest_metadata()
    
    # Output digest text first
    print(digest_text)
    
    # If we have stories, output feedback card instructions
    if metadata.get('stories'):
        feedback = generate_feedback_card(metadata['stories'])
        if feedback:
            print("\n---FEEDBACK_CARD---")
            print(json.dumps(feedback))

if __name__ == "__main__":
    main()
