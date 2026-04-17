#!/usr/bin/env python3
"""
Parse feedback from knos-digest markdown files
Reads checkboxes and notes to extract user engagement patterns
"""
import re
import json
from pathlib import Path
from datetime import datetime
from feedback_handler import record_feedback, init_db

def parse_story_block(lines, start_idx):
    """
    Parse a single story block starting at start_idx
    Returns: (story_data, next_idx) or (None, next_idx)
    """
    if start_idx >= len(lines):
        return None, start_idx
    
    line = lines[start_idx].strip()
    
    # Check if this is a story item (starts with checkbox)
    checkbox_match = re.match(r'^- \[([ x])\]\s*(.+)$', line)
    if not checkbox_match:
        return None, start_idx + 1
    
    checked = checkbox_match.group(1) == 'x'
    title_line = checkbox_match.group(2)
    
    # Extract title (may have emoji prefix)
    title = re.sub(r'^(📰|💬|🔥)\s*', '', title_line).strip()
    
    # Parse subsequent lines for metadata
    story_data = {
        'checked': checked,
        'title': title,
        'score': None,
        'karma': None,
        'author': None,
        'url': None,
        'story_id': None,
        'notes': ''
    }
    
    idx = start_idx + 1
    while idx < len(lines):
        line = lines[idx].strip()
        
        # Stop at next story or section
        if line.startswith('- ['):
            break
        if line.startswith('*') and line.endswith('*'):  # Section header
            break
        if line.startswith('🎯') or line.startswith('_Keep building'):
            break
        
        # Parse metadata line (↑score | karma: X | by author)
        meta_match = re.search(r'↑(\d+)\s*\|\s*(?:karma:\s*(\d+[,\d]*)\s*\|)?\s*by\s+(\w+)', line)
        if meta_match:
            story_data['score'] = int(meta_match.group(1))
            if meta_match.group(2):
                story_data['karma'] = int(meta_match.group(2).replace(',', ''))
            story_data['author'] = meta_match.group(3)
        
        # Parse URL (🔗 link)
        url_match = re.search(r'🔗\s+(https?://[^\s]+)', line)
        if url_match:
            url = url_match.group(1)
            story_data['url'] = url
            # Extract HN story ID if present
            id_match = re.search(r'item\?id=(\d+)', url)
            if id_match:
                story_data['story_id'] = id_match.group(1)
        
        # Parse notes
        if line.startswith('Notes:'):
            notes_text = line[6:].strip()
            # Continue reading until next story or section
            note_lines = [notes_text] if notes_text else []
            idx += 1
            while idx < len(lines):
                next_line = lines[idx].strip()
                if next_line.startswith('- [') or next_line.startswith('*'):
                    break
                if next_line.startswith('🎯') or next_line.startswith('_'):
                    break
                if next_line:
                    note_lines.append(next_line)
                idx += 1
            story_data['notes'] = '\n'.join(note_lines).strip()
            break
        
        idx += 1
    
    return story_data, idx

def parse_digest_file(filepath):
    """Parse a single digest markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    stories = []
    
    idx = 0
    while idx < len(lines):
        story, next_idx = parse_story_block(lines, idx)
        if story:
            stories.append(story)
        idx = next_idx
    
    return stories

def extract_feedback_from_story(story, digest_date):
    """
    Determine feedback action from story data
    
    Rules:
    - [x] with notes = save (want to revisit)
    - [x] without notes = like (engaged)
    - [ ] = skip (ignored)
    """
    if story['checked']:
        if story['notes']:
            return 'save'
        else:
            return 'like'
    else:
        return 'skip'

def process_knos_digests(directory='knos-digest', days_back=30):
    """
    Process all digest markdown files in directory
    Extract and store feedback
    """
    knos_dir = Path(__file__).parent / directory
    if not knos_dir.exists():
        print(f"Error: {knos_dir} not found")
        return {'status': 'error', 'message': 'Directory not found'}
    
    # Get all .md files
    md_files = sorted(knos_dir.glob('*.md'))
    if not md_files:
        print(f"No markdown files found in {knos_dir}")
        return {'status': 'error', 'message': 'No files to process'}
    
    # Filter by date if specified
    cutoff_date = None
    if days_back:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_back)
    
    conn = init_db()
    c = conn.cursor()
    
    # Add notes column if it doesn't exist (do this upfront)
    c.execute("PRAGMA table_info(feedback)")
    columns = [col[1] for col in c.fetchall()]
    if 'notes' not in columns:
        c.execute("ALTER TABLE feedback ADD COLUMN notes TEXT")
        conn.commit()
    
    results = {
        'files_processed': 0,
        'stories_found': 0,
        'feedback_recorded': 0,
        'feedback_breakdown': {'like': 0, 'save': 0, 'skip': 0},
        'errors': []
    }
    
    for md_file in md_files:
        # Extract date from filename (YYYY-MM-DD.md)
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', md_file.stem)
        if not date_match:
            continue
        
        digest_date = date_match.group(1)
        print(f"Processing {digest_date}...", flush=True)
        
        # Skip if older than cutoff
        if cutoff_date:
            try:
                file_date = datetime.strptime(digest_date, '%Y-%m-%d')
                if file_date < cutoff_date:
                    continue
            except ValueError:
                continue
        
        try:
            stories = parse_digest_file(md_file)
            results['files_processed'] += 1
            results['stories_found'] += len(stories)
            
            for story in stories:
                # Skip if no story_id (can't track without it)
                if not story['story_id']:
                    continue
                
                # Check if already recorded
                c.execute(
                    "SELECT id FROM feedback WHERE story_id = ? AND digest_date = ?",
                    (story['story_id'], digest_date)
                )
                if c.fetchone():
                    continue  # Already recorded
                
                action = extract_feedback_from_story(story, digest_date)
                
                # Build metadata
                metadata = {
                    'title': story['title'],
                    'url': story['url'],
                    'score': story['score'],
                    'by': story['author']
                }
                
                # Record feedback
                record_feedback(
                    story_id=story['story_id'],
                    action=action,
                    metadata=metadata
                )
                
                # Store notes separately if present
                if story['notes']:
                    c.execute(
                        """UPDATE feedback 
                           SET notes = ? 
                           WHERE story_id = ? AND digest_date = ?""",
                        (story['notes'], story['story_id'], digest_date)
                    )
                
                results['feedback_recorded'] += 1
                results['feedback_breakdown'][action] += 1
        
        except Exception as e:
            results['errors'].append({
                'file': str(md_file),
                'error': str(e)
            })
    
    conn.commit()
    conn.close()
    
    return results

def main():
    """CLI interface"""
    import sys
    
    days_back = 30
    if len(sys.argv) > 1:
        days_back = int(sys.argv[1])
    
    print(f"🔍 Scanning knos-digest files (last {days_back} days)...", flush=True)
    results = process_knos_digests(days_back=days_back)
    
    print(f"\n✅ Results:", flush=True)
    print(f"   Files processed: {results['files_processed']}", flush=True)
    print(f"   Stories found: {results['stories_found']}", flush=True)
    print(f"   Feedback recorded: {results['feedback_recorded']}", flush=True)
    print(f"\n📊 Breakdown:", flush=True)
    for action, count in results['feedback_breakdown'].items():
        emoji = {'like': '👍', 'save': '📌', 'skip': '👎'}[action]
        print(f"   {emoji} {action}: {count}", flush=True)
    
    if results['errors']:
        print(f"\n⚠️  Errors: {len(results['errors'])}", flush=True)
        for err in results['errors']:
            print(f"   {err['file']}: {err['error']}", flush=True)
    
    print(f"\n💾 Feedback stored in: knowledge-os/hn_feedback.db", flush=True)

if __name__ == "__main__":
    main()
