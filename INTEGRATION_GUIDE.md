# Integration Guide: Engagement Features

## Quick Start (15 minutes)

### 1. Add Engagement Detection to Digest Pipeline

**File:** `process_digest.py`

Add at top:
```python
from engagement_impl import EngagementDetector, format_engagement_section
```

After story matching, before formatting output:
```python
# Existing code generates matched_stories
# ...

# NEW: Detect engagement opportunities
detector = EngagementDetector('hn_digest_v2.db')
opportunities = detector.detect_opportunities(matched_stories, max_results=3)
detector.save_opportunities(opportunities, datetime.now().date().isoformat())

# Format for digest
engagement_section = format_engagement_section(opportunities)
```

### 2. Update Digest Output Format

**File:** `send_digest.py` (or wherever you format the WhatsApp message)

Current format:
```python
message = f"""🦅 *HN Digest* - {date}

📚 Stories Matched
{stories_section}

👤 Author Watch
{authors_section}
"""
```

New format:
```python
message = f"""🦅 *HN Digest* - {date}

📚 Stories Matched
{stories_section}

{engagement_section}  # NEW

👤 Author Watch
{authors_section}
"""
```

### 3. Test Run

```bash
cd /Users/vb/.openclaw/workspace/hn-digest
python3 engagement_impl.py  # Test standalone
./run_digest_v2.sh          # Test full pipeline
```

---

## Advanced: Engagement Tracking

### Track Your Comments

When you comment on HN, record it:

```bash
# Quick CLI tool (create as track_engagement.sh)
#!/bin/bash
story_id=$1
comment_url=$2
karma=${3:-0}

python3 -c "
from engagement_impl import EngagementDetector
detector = EngagementDetector('hn_digest_v2.db')
detector.mark_engaged($story_id, '$comment_url', $karma)
print('✅ Engagement tracked')
"
```

Usage:
```bash
./track_engagement.sh 12345 "https://news.ycombinator.com/item?id=67890" 5
```

### Weekly Engagement Report

Create `report_engagement.py`:

```python
#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

db = sqlite3.connect('hn_digest_v2.db')
c = db.cursor()

# Last 7 days
week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()

c.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN engaged = 1 THEN 1 ELSE 0 END) as engaged,
        SUM(karma_gained) as karma
    FROM engagement_opportunities 
    WHERE detected_date >= ?
''', (week_ago,))

total, engaged, karma = c.fetchone()
rate = (engaged / total * 100) if total > 0 else 0

print(f"""
📊 Weekly Engagement Report

Opportunities detected: {total}
Engaged with: {engaged} ({rate:.1f}%)
Karma gained: {karma or 0}
""")

# Top opportunities you engaged with
c.execute('''
    SELECT s.title, eo.karma_gained, eo.comment_url
    FROM engagement_opportunities eo
    JOIN stories s ON eo.story_id = s.id
    WHERE eo.engaged = 1 AND eo.detected_date >= ?
    ORDER BY eo.karma_gained DESC
    LIMIT 5
''', (week_ago,))

print("Top engagements:")
for title, karma, url in c.fetchall():
    print(f"  • {title[:60]}... ({karma or 0} karma)")

db.close()
```

Run weekly: `python3 report_engagement.py`

---

## Iteration Plan

### Week 1: Basic Detection
- Run with simple filters (Ask/Show HN, low comments)
- Observe: are these actually good opportunities?
- Track: how many do you engage with?

### Week 2: Scoring Refinement
- Adjust weights based on engagement rate
- Add more signals (author karma, topic strength)
- Test different max_results (3 vs 5 vs 10)

### Week 3: Comment Analysis
- Fetch actual comments for matched stories
- Detect unanswered questions
- Identify debate patterns
- Add these as new opportunity types

### Week 4: Context Enrichment
- Cross-reference with your blog posts
- Match stories to your project domains
- Generate specific angle suggestions

---

## Example Output

Before (current digest):
```
🦅 HN Digest - 2026-02-16

📚 Stories Matched
• ML monitoring in production (45 points, 12h ago)
• Parenting with data-driven feedback (78 points, 5h ago)

👤 Author Watch
• pg posted about startup advice
```

After (with engagement):
```
🦅 HN Digest - 2026-02-16

📚 Stories Matched
• ML monitoring in production (45 points, 12h ago)
• Parenting with data-driven feedback (78 points, 5h ago)

🎯 Engagement Opportunities

💬 Ask HN: Best practices for knowledge graphs in production?
   → Direct question. 3 comments so far. Share your experience?
   https://news.ycombinator.com/item?id=12345

🎯 Discussion: Concept drift vs data drift in ML models
   → Early conversation (2 comments). High visibility opportunity. Add value?
   https://news.ycombinator.com/item?id=67890

👤 Author Watch
• pg posted about startup advice
```

---

## Metrics to Track

After 1 month, review:

| Metric | Target | Actual |
|--------|--------|--------|
| Opportunities/week | 15-20 | ___ |
| Engagement rate | 20-30% | ___ |
| Avg karma/comment | 3+ | ___ |
| Replies/comment | 1+ | ___ |
| Time to engage | <2h | ___ |

Adjust strategy based on results.

---

## FAQ

**Q: What if there are no good opportunities on a given day?**  
A: Skip the engagement section entirely. Quality > consistency.

**Q: Should I comment on every opportunity?**  
A: No. Pick 1-2 per week that genuinely excite you. The digest is an aid, not a mandate.

**Q: How do I avoid self-promotion spam?**  
A: Only link your blog/projects when they add genuine value. Lead with insight, not links.

**Q: What if my comments get downvoted?**  
A: Learn from it. Review what worked vs what didn't. Adjust scoring to surface better opportunities.

---

_Implementation time: ~1 hour. Iteration cycle: weekly for first month._
