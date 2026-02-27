# knowledge-os

**Intelligent HN digest with semantic topic matching and engagement opportunity detection.**

Daily curated Hacker News stories delivered via WhatsApp at 2 PM, personalized to your interests (AI/ML, Data Science, Parenting, Philosophy) with actionable engagement opportunities.

---

## High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Daily Pipeline (2 PM)                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼────────┐       ┌────────▼────────┐
            │  Fetch Stories │       │   Load Config   │
            │   (HN API)     │       │  Topics, User   │
            └───────┬────────┘       └────────┬────────┘
                    │                         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Semantic Matching     │
                    │  (sentence-transformer)  │
                    │   Topic embeddings vs    │
                    │   Story embeddings       │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼─────┐  ┌──────▼──────┐  ┌─────▼─────────┐
        │   Stories    │  │   Authors   │  │  Engagement   │
        │   Matched    │  │   Tracking  │  │  Detection    │
        │  (by topic)  │  │ (continuity)│  │ (opportunities)│
        └───────┬──────┘  └──────┬──────┘  └─────┬─────────┘
                │                │                │
                └────────────────┼────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Store to SQLite       │
                    │  (stories, topics,      │
                    │   authors, engagement)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Format Digest         │
                    │  (WhatsApp markdown)    │
                    │  + Engagement section   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Send via WhatsApp     │
                    │   Archive to file       │
                    └─────────────────────────┘
```

---

## System Components

### 1. Story Fetching (`fetch_stories.py`, `fetch_substack.py`)
- **HN Input:** HN topstories API → `stories_raw.json`
- **Substack Input:** RSS feeds (configured in `config.json` under `sources.substack`) → `substack_raw.json`
- **Output:** Merged `all_stories.json` with uniform schema
- **Fields:** id, title, url, score, by (author), descendants (comment count), time, source
- **Substack stories** get `score: 0`, `descendants: 0`, and `source: "substack"` (marked with 📰 in digest)

### 2. Topic Matching (`match_topics.py`)
- **Method:** Semantic similarity (sentence-transformers)
- **Model:** `all-MiniLM-L6-v2` (lightweight, fast)
- **Topics:** Defined in `config.json` with keyword lists
- **Threshold:** Configurable similarity score (0.3 default)
- **Output:** Stories with topic scores, best match selected

### 3. Storage Layer (`storage_sqlite.py`)
- **Database:** `hn_digest_v2.db` (SQLite)
- **Tables:**
  - `users` - User profiles
  - `topics` - Topic definitions with weights
  - `items` - HN stories (deduplicated)
  - `item_topic_scores` - Story-topic similarity scores
  - `authors` - Author stats across topics
  - `digests` - Delivery history
  - `feedback` - User actions (delivered, clicked, etc.)
  - `engagement_opportunities` - Detected opportunities
  - `user_comments` - VB's HN comments (auto-synced)
  - `engagement_stats` - Weekly engagement metrics

### 4. Engagement Detection (`engagement.py`)
- **Input:** Matched stories from digest pipeline
- **Detection types:**
  - **Ask/Show HN:** Explicit feedback requests (score 0.75+)
  - **Early threads:** <10 comments, <6h old (score 0.55+)
  - **Hot debates:** 50+ comments, active (score 0.45+)
- **Comment analysis:** Top 3 opportunities analyzed for questions/debates
- **Scoring boosts:**
  - Has questions: +0.15
  - Has debate: +0.10
- **Output:** Top 5 scored opportunities
- **Auto-tracking:** Syncs vb7132's HN comments, marks engaged opportunities

### 5. Digest Processing (`process_digest.py`)
- **Main pipeline:** Orchestrates all components
- **Steps:**
  1. Load config
  2. Initialize storage
  3. Match topics to stories
  4. Track authors
  5. Detect engagement opportunities
  6. Format digest
  7. Return structured result

### 6. Delivery (`send_digest.py`)
- **Format:** WhatsApp markdown
- **Sections:**
  - Stories matched (by topic)
  - Engagement opportunities (5)
  - Notable authors (3)
- **Archive:** Saves to:
  - `knos-digest/YYYY-MM-DD.md` (primary, markdown format)
  - `archive/YYYY-MM-DD_digest.txt` (legacy, backward compatibility)
- **Scheduling:** `daily_digest.sh` via cron (2 PM daily)

---

## Data Flow

### Daily Digest Flow

```
1. FETCH (fetch_stories.py)
   ├─ GET https://hacker-news.firebaseio.com/v0/topstories.json
   ├─ Fetch top 100 story details
   └─ Save to stories_raw.json

2. MATCH (match_topics.py via process_digest.py)
   ├─ Load sentence-transformer model
   ├─ Generate story embeddings
   ├─ Compare to topic embeddings (config.json)
   ├─ Calculate similarity scores
   └─ Select best topic match per story (threshold: 0.3)

3. STORE (storage_sqlite.py)
   ├─ Check if story already seen (deduplication)
   ├─ Insert new stories → items table
   ├─ Insert topic scores → item_topic_scores
   ├─ Update author stats → authors table
   └─ Record digest → digests table

4. ENGAGE (engagement.py)
   ├─ Detect Ask/Show HN stories
   ├─ Detect early threads (<10 comments)
   ├─ Detect hot debates (50+ comments)
   ├─ Fetch comments for top 3 (HN API)
   ├─ Analyze for questions/debates
   ├─ Score and rank opportunities
   ├─ Save to engagement_opportunities table
   └─ Sync vb7132's recent comments (auto-track engagement)

5. FORMAT (process_digest.py → generate_digest_text)
   ├─ Group stories by topic
   ├─ Mark notable authors with ⭐
   ├─ Add engagement opportunities section
   ├─ Format for WhatsApp markdown
   └─ Add motivational footer

6. DELIVER (send_digest.py)
   ├─ Send to WhatsApp (OpenClaw gateway)
   ├─ Archive to archive/YYYY-MM-DD_digest.txt
   └─ Log feedback (delivered)
```

---

## Configuration

### Topics (`config.json`)

```json
{
  "topics": [
    {
      "name": "AI/ML/LLMs",
      "keywords": ["ai", "machine learning", "llm", "gpt", ...],
      "weight": 1.0
    },
    {
      "name": "Data Science",
      "keywords": ["data science", "pandas", "statistics", ...],
      "weight": 1.0
    },
    ...
  ],
  "user": {
    "identifier": "vb@knowledge-os"
  },
  "settings": {
    "notable_author_threshold": 3,
    "max_stories_per_digest": 10
  }
}
```

### Storage Backend

```json
{
  "storage": {
    "backend": "sqlite",
    "sqlite": {
      "db_path": "hn_digest_v2.db"
    }
  }
}
```

---

## File Structure

```
knowledge-os/
├── README.md                    # This file
├── SAMPLE_OUTPUT.md             # Example digest output
├── DAILY_FLOW.md                # Summary vs Digest comparison
├── ARCHITECTURE.md              # Detailed architecture docs
├── ENGAGEMENT.md                # Engagement strategy (Feb 16)
├── ENGAGEMENT_PLAN.md           # Implementation details
├── ENGAGEMENT_SUMMARY_PLAN.md   # Summary design & delivery options
├── INTEGRATION_GUIDE.md         # Integration guide (Feb 16)
├── NEXT.md                      # Roadmap
│
├── config.json                  # Topic definitions, settings
│
├── Core Pipeline
├── fetch_stories.py             # HN API fetcher
├── fetch_substack.py            # Substack RSS fetcher
├── match_topics.py              # Semantic topic matcher
├── process_digest.py            # Main orchestration
├── engagement.py                # Engagement detection + tracking
│
├── Storage Layer
├── storage_interface.py         # Abstract storage interface
├── storage_sqlite.py            # SQLite implementation
│
├── Delivery
├── send_digest.py               # WhatsApp sender + archiver
├── daily_digest.sh              # Digest cron wrapper (2 PM)
├── run_digest_v2.sh             # Full digest pipeline
├── engagement_summary.py        # Summary generator (9 AM)
├── send_engagement_summary.sh   # Summary delivery wrapper
│
├── Testing
├── tests/                       # pytest test suite (7 test files)
├── test_engagement.sh           # Engagement module tests (legacy)
│
├── Data
├── hn_digest_v2.db              # SQLite database
├── stories_raw.json             # Last HN fetch
├── knos-digest/                 # Daily digest archive (markdown)
│   ├── 2026-02-20.md
│   └── ...
├── archive/                     # Legacy archive (backward compat)
│   ├── 2026-02-20_digest.txt
│   └── ...
│
└── Legacy (deprecated)
    ├── run_digest.sh
    ├── generate_digest.py
    └── ...
```

---

## Usage

### Daily Messages (Automatic)

**Two separate messages at different times:**

1. **Engagement Summary (9:00 AM)**
   - Yesterday's engagement reflection
   - Comments posted, opportunities engaged
   - 7-day trend + tips
   - Only sent when you engaged yesterday

2. **HN Digest (2:00 PM)**
   - Today's matched stories
   - 5 engagement opportunities
   - Notable authors

See [DAILY_FLOW.md](DAILY_FLOW.md) for detailed comparison.

### Manual Commands

**Run digest pipeline:**
```bash
cd /Users/vb/.openclaw/workspace/knowledge-os
./run_digest_v2.sh
```

**Test engagement module:**
```bash
./test_engagement.sh
```

**Check engagement stats:**
```bash
python3 engagement.py
```

**Generate engagement summary (yesterday):**
```bash
python3 engagement_summary.py
```

### Scheduled Delivery

```bash
# Digest: 2 PM daily
0 14 * * * /Users/vb/.openclaw/workspace/knowledge-os/daily_digest.sh

# Summary: 9 AM daily (to be added)
0 9 * * * /Users/vb/.openclaw/workspace/knowledge-os/send_engagement_summary.sh
```

---

## Engagement Workflow

### For You (VB)

**Daily (2:00 PM):**
1. Receive digest via WhatsApp
2. Scan 🎯 Engagement Opportunities section (30 seconds)
3. Pick 1 opportunity if something resonates (not obligatory)
4. Draft comment (5 minutes, add genuine value)
5. Post on HN within 2 hours (while story is hot)

**System auto-tracks:**
- Fetches vb7132's recent HN comments
- Traces parent chain to find story ID
- Marks opportunities as "engaged" automatically
- Calculates engagement rate weekly

**Weekly (Mondays):**
```bash
python3 engagement.py  # Check stats
```

Review:
- Opportunities detected
- Engagement rate (target: 20-40%)
- Comments posted
- Iterate on scoring/prompts if needed

---

## Key Metrics

### Content Quality
- **Stories/digest:** 4-10 (semantic matches)
- **Topics covered:** AI/ML, Data Science, Parenting, Philosophy
- **Deduplication:** SQLite prevents re-showing stories

### Engagement (30-Day Target)
| Metric | Target | Why |
|--------|--------|-----|
| Opportunities/week | 30-35 (5/day) | Consistent flow |
| Engagement rate | 20-40% (6-14/week) | Quality filter |
| Avg karma/comment | 3+ | Signal quality |
| Replies/comment | 1+ | Conversation starter |

**Review date:** March 20, 2026

---

## Technology Stack

- **Language:** Python 3.9+
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Database:** SQLite 3
- **API:** HN Firebase API
- **Delivery:** OpenClaw (WhatsApp gateway)
- **Scheduling:** cron

---

## Architecture Principles

1. **Semantic over keywords:** Embeddings capture intent, not just word matches
2. **Continuity:** Author tracking across digests, deduplication
3. **Leverage:** Engagement detection automates opportunity discovery
4. **Feedback loop:** Auto-tracking engagement improves scoring
5. **Modularity:** Storage layer abstraction, pluggable backends
6. **MVP → iterate:** Ship fast, refine based on usage

---

## Recent Updates

**2026-02-27:** Multi-source support + test coverage
- Substack RSS fetcher (`fetch_substack.py`) with config-driven feeds
- 📰 source indicator in digest for Substack articles
- Pipeline integration test (`tests/test_pipeline_integration.py`)
- Read tracker, YC links, and unit tests marked complete in roadmap

**2026-02-20:** Engagement detection integrated + digest archive restructure
- 5 opportunities/day (Ask/Show HN, early threads, debates)
- Username tracking (vb7132) with auto-sync
- Comment analysis for top 3 opportunities (middle ground)
- Database tables added (engagement_opportunities, user_comments, engagement_stats)
- New archive format: `knos-digest/YYYY-MM-DD.md` (markdown, cleaner naming)
- Migrated 8 existing digests to new format

**2026-02-13:** Storage v2 architecture
- SQLite backend with author tracking
- Notable authors feature (⭐ marker)
- Digest history and feedback logging

**2026-02-11:** Initial launch
- Semantic topic matching
- Daily WhatsApp delivery at 2 PM

---

## Future Work

See [NEXT.md](NEXT.md) for detailed roadmap.

**Immediate:**
- Monitor engagement quality for first 30 days
- Iterate on scoring based on VB's engagement patterns

**Mid-term:**
- Author reputation weighting (HN karma)
- Trend detection ("this topic is heating up")
- Dynamic topic learning from engagement

**Long-term:**
- Multi-source feeds (Reddit, ArXiv)
- Knowledge graph integration
- Voice summaries for commute listening

---

## Sample Output

See [SAMPLE_OUTPUT.md](SAMPLE_OUTPUT.md) for full example digest.

---

## License

Personal project for VB. Not for public distribution.

---

_Built with OpenClaw by Crow 🦅_
