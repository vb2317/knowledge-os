#!/usr/bin/env python3
"""
Handle feedback from HN digest buttons
Stores feedback in SQLite for pattern learning

FUTURE: WhatsApp Business API Integration
- Current: Simple reply parsing (text format: "1,3 👍  2 📌")
- Planned: Inline buttons via WhatsApp Business API
- Callback format: hn_like:{story_id}, hn_save:{story_id}, hn_skip:{story_id}
- This handler works with both approaches (just parse callback_data instead)
- See: knowledge-os/PLANNED.md
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "hn_feedback.db"

def init_db():
    """Initialize feedback database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Feedback table
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  story_id TEXT,
                  story_title TEXT,
                  story_url TEXT,
                  story_score INTEGER,
                  story_author TEXT,
                  action TEXT,
                  timestamp TEXT,
                  digest_date TEXT)''')
    
    # Aggregated patterns
    c.execute('''CREATE TABLE IF NOT EXISTS patterns
                 (category TEXT PRIMARY KEY,
                  liked_count INTEGER DEFAULT 0,
                  saved_count INTEGER DEFAULT 0,
                  skipped_count INTEGER DEFAULT 0,
                  last_updated TEXT)''')
    
    conn.commit()
    return conn

def record_feedback(story_id, action, metadata=None):
    """Record user feedback on a story
    
    Args:
        story_id: HN story ID
        action: 'like', 'save', or 'skip'
        metadata: dict with story details (title, url, score, author)
    """
    conn = init_db()
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    today = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''INSERT INTO feedback 
                 (story_id, story_title, story_url, story_score, story_author, 
                  action, timestamp, digest_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (story_id,
               metadata.get('title', '') if metadata else '',
               metadata.get('url', '') if metadata else '',
               metadata.get('score', 0) if metadata else 0,
               metadata.get('by', '') if metadata else '',
               action,
               now,
               today))
    
    conn.commit()
    conn.close()
    
    return {
        'status': 'recorded',
        'story_id': story_id,
        'action': action,
        'timestamp': now
    }

def get_feedback_stats(days=30):
    """Get feedback statistics for recent period"""
    conn = init_db()
    c = conn.cursor()
    
    # Overall stats
    c.execute('''SELECT action, COUNT(*) as count
                 FROM feedback
                 WHERE timestamp >= datetime('now', '-' || ? || ' days')
                 GROUP BY action''', (days,))
    
    overall = {row[0]: row[1] for row in c.fetchall()}
    
    # Top liked authors
    c.execute('''SELECT story_author, COUNT(*) as likes
                 FROM feedback
                 WHERE action = 'like' 
                   AND timestamp >= datetime('now', '-' || ? || ' days')
                 GROUP BY story_author
                 ORDER BY likes DESC
                 LIMIT 10''', (days,))
    
    top_authors = [{'author': row[0], 'likes': row[1]} for row in c.fetchall()]
    
    # Top saved stories
    c.execute('''SELECT story_title, story_url, story_author
                 FROM feedback
                 WHERE action = 'save'
                   AND timestamp >= datetime('now', '-' || ? || ' days')
                 ORDER BY timestamp DESC
                 LIMIT 10''', (days,))
    
    saved_stories = [
        {'title': row[0], 'url': row[1], 'author': row[2]}
        for row in c.fetchall()
    ]
    
    conn.close()
    
    return {
        'overall': overall,
        'top_authors': top_authors,
        'saved_stories': saved_stories,
        'period_days': days
    }

def main():
    """CLI interface for feedback handler"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: feedback_handler.py <story_id> <action> [metadata_json]")
        print("Actions: like, save, skip")
        sys.exit(1)
    
    story_id = sys.argv[1]
    action = sys.argv[2]
    metadata = None
    
    if len(sys.argv) > 3:
        metadata = json.loads(sys.argv[3])
    
    result = record_feedback(story_id, action, metadata)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
