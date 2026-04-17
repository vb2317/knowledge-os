#!/usr/bin/env python3
"""
Agent script to send HN digest with feedback buttons
Outputs instructions for the agent to follow
"""
import json
from pathlib import Path

def main():
    # Load digest text
    digest_path = Path(__file__).parent / "digest.txt"
    metadata_path = Path(__file__).parent / "digest_metadata.json"
    
    if not digest_path.exists():
        print("Error: digest.txt not found")
        return
    
    with open(digest_path) as f:
        digest_text = f.read()
    
    # Load metadata if available
    metadata = {"stories": []}
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
    
    stories = metadata.get('stories', [])
    
    # Output instructions for the agent
    print("📤 SEND DIGEST TO WHATSAPP")
    print("=" * 60)
    print()
    print("Step 1: Send the digest text")
    print("-" * 60)
    print(digest_text)
    print()
    
    if stories:
        print("=" * 60)
        print()
        print("Step 2: Send feedback card with buttons")
        print("-" * 60)
        print()
        print(f"Found {len(stories)} stories for feedback")
        print()
        print("Use the message tool with action=send and buttons parameter:")
        print()
        print("Message text:")
        print("---")
        print("📊 *Quick Feedback*")
        print()
        print("Rate today's stories to improve future digests:")
        print()
        for idx, story in enumerate(stories, 1):
            title = story['title'][:50] + "..." if len(story['title']) > 50 else story['title']
            print(f"{idx}. {title}")
        print("---")
        print()
        print("Buttons JSON:")
        print("---")
        
        # Generate button rows
        buttons = []
        for idx, story in enumerate(stories, 1):
            story_id = story.get('id', f"story_{idx}")
            row = [
                {"text": f"{idx} 👍", "callback_data": f"hn_like:{story_id}"},
                {"text": f"{idx} 📌", "callback_data": f"hn_save:{story_id}"},
                {"text": f"{idx} 👎", "callback_data": f"hn_skip:{story_id}"}
            ]
            buttons.append(row)
        
        print(json.dumps(buttons, indent=2))
        print("---")
        print()
        print("💡 When user taps a button, the callback_data will be sent.")
        print("   Handler: /Users/vb/.openclaw/workspace/knowledge-os/feedback_handler.py")

if __name__ == "__main__":
    main()
