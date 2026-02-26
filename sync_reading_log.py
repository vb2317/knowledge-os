#!/usr/bin/env python3
"""
Parse checked items from a digest .md file and sync read status to the DB.

Usage:
    venv/bin/python sync_reading_log.py knos-digest/2026-02-24.md
"""
import re
import sys
import json
from storage_interface import get_storage


def parse_read_items(md_text: str) -> list[dict]:
    """
    Parse checked read-tracker items from digest markdown.

    Returns list of dicts: {'title': str, 'score': int, 'note': str}
    """
    results = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^- \[x\] (.+?) \(↑(\d+)\)\s*$', line, re.IGNORECASE)
        if m:
            title = m.group(1)
            score = int(m.group(2))
            note = ""
            # Check next line for notes
            if i + 1 < len(lines):
                note_match = re.match(r'^\s+Notes:\s*(.*)', lines[i + 1])
                if note_match:
                    note = note_match.group(1).strip()
            results.append({'title': title, 'score': score, 'note': note})
        i += 1
    return results


def sync_to_db(read_items: list[dict], config_path: str = "config.json") -> list[dict]:
    """
    Look up each read item in the DB and insert feedback.
    Returns list of synced items with their item_ids.
    """
    with open(config_path) as f:
        config = json.load(f)

    storage_config = config['storage']
    storage = get_storage(
        backend=storage_config['backend'],
        **storage_config.get(storage_config['backend'], {})
    )

    user_id = storage.get_or_create_user(config['user']['identifier'])

    synced = []
    for item in read_items:
        # Search by title match in items table
        conn = storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT item_id, title FROM items WHERE title = ?', (item['title'],))
        row = c.fetchone()
        conn.close()

        if not row:
            print(f"  [skip] Not found in DB: {item['title']}")
            continue

        item_id = row['item_id']
        action = 'read_with_note' if item['note'] else 'read'
        metadata = {'note': item['note']} if item['note'] else None

        storage.insert_feedback(
            user_id=user_id,
            item_id=item_id,
            action=action,
            metadata=metadata
        )
        synced.append({'item_id': item_id, 'title': item['title'], 'action': action})
        print(f"  [synced] {action}: {item['title']}")

    return synced


def main():
    if len(sys.argv) < 2:
        print("Usage: sync_reading_log.py <digest.md>")
        sys.exit(1)

    md_path = sys.argv[1]
    with open(md_path) as f:
        md_text = f.read()

    read_items = parse_read_items(md_text)
    if not read_items:
        print("No checked items found.")
        return

    print(f"Found {len(read_items)} checked item(s):")
    synced = sync_to_db(read_items)
    print(f"\nSynced {len(synced)} item(s) to DB.")


if __name__ == "__main__":
    main()
