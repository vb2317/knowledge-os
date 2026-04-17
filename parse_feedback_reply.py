#!/usr/bin/env python3
"""
Parse feedback from natural WhatsApp reply text
Handles formats like:
- "1,3 👍  2 📌  4,5 skip"
- "like 1,3,5"
- "save 2 | skip 4,5"
- "1 👍 2 📌 3 👎"
"""
import re
import json
from pathlib import Path
from feedback_handler import record_feedback

# Action keywords and emoji mapping
ACTION_MAP = {
    'like': ['like', '👍', '⭐', 'good', 'yes', 'interesting'],
    'save': ['save', '📌', '💾', 'bookmark', 'read'],
    'skip': ['skip', '👎', '❌', 'no', 'pass', 'ignore']
}

def load_current_stories():
    """Load story metadata from today's digest"""
    metadata_path = Path(__file__).parent / "digest_metadata.json"
    if not metadata_path.exists():
        return []
    
    with open(metadata_path) as f:
        data = json.load(f)
        return data.get('stories', [])

def normalize_action(word):
    """Convert various inputs to standard action"""
    word = word.lower().strip()
    for action, patterns in ACTION_MAP.items():
        if word in patterns:
            return action
    return None

def parse_feedback(text):
    """
    Parse feedback text into structured actions
    
    Returns: [(story_number, action), ...]
    """
    text = text.lower().strip()
    results = []
    
    # Pattern 1: "action number,number" format
    # Example: "like 1,3,5" or "save 2"
    action_patterns = [
        r'(like|save|skip)\s+([\d,\s]+)',
        r'(👍|📌|👎)\s+([\d,\s]+)',
        r'([\d,\s]+)\s+(like|save|skip|👍|📌|👎)'
    ]
    
    for pattern in action_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            if match.group(1).isdigit() or ',' in match.group(1):
                numbers_str = match.group(1)
                action_str = match.group(2)
            else:
                action_str = match.group(1)
                numbers_str = match.group(2)
            
            action = normalize_action(action_str)
            if not action:
                continue
            
            # Parse numbers
            numbers = []
            for num_str in re.findall(r'\d+', numbers_str):
                numbers.append(int(num_str))
            
            for num in numbers:
                results.append((num, action))
    
    # Pattern 2: "number action number action" format
    # Example: "1 👍 2 📌 3 👎"
    inline_pattern = r'(\d+)\s*([👍📌👎]|like|save|skip)'
    matches = re.finditer(inline_pattern, text)
    for match in matches:
        num = int(match.group(1))
        action = normalize_action(match.group(2))
        if action:
            results.append((num, action))
    
    # Deduplicate (last action wins for each story number)
    final = {}
    for num, action in results:
        final[num] = action
    
    return [(num, action) for num, action in final.items()]

def process_feedback(text):
    """
    Process feedback text and record in database
    
    Returns: Summary of recorded feedback
    """
    stories = load_current_stories()
    if not stories:
        return {
            'status': 'error',
            'message': 'No digest metadata found. Generate digest first.'
        }
    
    parsed = parse_feedback(text)
    if not parsed:
        return {
            'status': 'error',
            'message': 'Could not parse feedback. Try format: "1,3 👍  2 📌  4 skip"'
        }
    
    recorded = []
    for story_num, action in parsed:
        if story_num < 1 or story_num > len(stories):
            continue
        
        story = stories[story_num - 1]  # 0-indexed
        result = record_feedback(
            story_id=str(story.get('id', f"story_{story_num}")),
            action=action,
            metadata=story
        )
        recorded.append({
            'story_number': story_num,
            'story_title': story['title'][:50] + "...",
            'action': action
        })
    
    return {
        'status': 'ok',
        'recorded': recorded,
        'count': len(recorded)
    }

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: parse_feedback_reply.py '<feedback text>'")
        print("Examples:")
        print("  parse_feedback_reply.py '1,3 👍  2 📌  4,5 skip'")
        print("  parse_feedback_reply.py 'like 1,3,5'")
        print("  parse_feedback_reply.py '1 👍 2 📌 3 👎'")
        sys.exit(1)
    
    feedback_text = ' '.join(sys.argv[1:])
    result = process_feedback(feedback_text)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
