# HN Digest Feedback System

## ✅ Current Implementation: Markdown Checkboxes

### How to Provide Feedback

**Method 1: Edit Markdown Files (Recommended)**
1. Open `knos-digest/YYYY-MM-DD.md` files
2. Check/uncheck boxes:
   - `[x]` = Engaged with this story (like)
   - `[ ]` = Skipped (not interested)
3. Add notes after `Notes:` line for stories you want to save
4. Run extraction: `./extract_feedback_simple.py 30`

**Method 2: WhatsApp Reply (Future)**
After receiving the digest, reply with story numbers and actions:

**Supported Formats:**
```
1,3 👍  2 📌  4,5 skip
like 1,3,5
1 👍 2 📌 3 👎
save 2 | skip 4,5
```

**Actions:**
- **👍 / like** - Story was interesting/valuable
- **📌 / save** - Want to read in detail later
- **👎 / skip** - Not relevant/not interested

### What Happens with Your Feedback

1. **Stored in SQLite** (`hn_feedback.db`)
   - Story metadata (title, author, score)
   - Your action (like/save/skip)
   - Timestamp

2. **Pattern Learning** (Future)
   - Authors you consistently like → boost their stories
   - Topics you skip → reduce similar content
   - Score thresholds that work for you

3. **Reading Queue** (Future)
   - Saved stories tracked separately
   - Can generate "saved stories" digest later

### Architecture

```
User Reply → parse_feedback_reply.py → feedback_handler.py → hn_feedback.db
                                                              ↓
                                                    Pattern Analysis
                                                              ↓
                                                    Future Digest Tuning
```

**Files:**
- ✅ `extract_feedback_simple.py` - Parse markdown checkboxes (current)
- ✅ `feedback_insights.sh` - Show analytics dashboard
- `parse_feedback_reply.py` - Natural language parser (future)
- `feedback_handler.py` - Database operations (future)
- `hn_feedback.db` - SQLite storage
- `digest_metadata.json` - Today's story metadata

### Quick Start

```bash
cd /Users/vb/.openclaw/workspace/knowledge-os

# Extract feedback from markdown files (last 30 days)
./extract_feedback_simple.py 30

# View analytics
./feedback_insights.sh
```

### Manual Processing (WhatsApp Replies - Future)

```bash
# Process feedback from command line
./parse_feedback_reply.py "1,3 👍  2 📌"

# View feedback stats
python3 -c "
from feedback_handler import get_feedback_stats
import json
stats = get_feedback_stats(days=30)
print(json.dumps(stats, indent=2))
"
```

### Future: WhatsApp Business API

See `PLANNED.md` for migration to inline buttons.

**Target UX:**
```
Story 1: Title...
[👍 Like] [📌 Save] [👎 Skip]

Story 2: Title...
[👍 Like] [📌 Save] [👎 Skip]
```

One tap instead of typing. Same backend, just different input method.

---

## Testing

```bash
# Test parser
cd knowledge-os
python3 -c "
from parse_feedback_reply import parse_feedback
print(parse_feedback('1,3 👍  2 📌  4,5 skip'))
"

# Test full flow (requires digest_metadata.json)
./parse_feedback_reply.py "1 👍 2 📌"
```

## Analytics Queries

```sql
-- Connect to database
sqlite3 /Users/vb/.openclaw/workspace/knowledge-os/hn_feedback.db

-- View all feedback
SELECT * FROM feedback ORDER BY timestamp DESC LIMIT 10;

-- Top liked authors
SELECT story_author, COUNT(*) as likes
FROM feedback
WHERE action = 'like'
GROUP BY story_author
ORDER BY likes DESC
LIMIT 10;

-- Saved stories
SELECT story_title, story_url, timestamp
FROM feedback
WHERE action = 'save'
ORDER BY timestamp DESC;

-- Action distribution
SELECT action, COUNT(*) as count
FROM feedback
GROUP BY action;
```
