# knowledge-os

**Multi-source digest pipeline with semantic topic matching, engagement detection, and inline read tracking.**

Curates stories from Hacker News and Substack RSS feeds, matches them to your interests via sentence-transformer embeddings, detects engagement opportunities, and delivers a daily digest via WhatsApp at 2 PM.

---

## How It Works

```
┌──────────────┐  ┌────────────────┐
│ fetch_stories│  │ fetch_substack │
│   (HN API)   │  │   (RSS feeds)  │
└──────┬───────┘  └───────┬────────┘
       │                  │
       └────────┬─────────┘
                ▼
       all_stories.json (merged)
                │
                ▼
     ┌──────────────────┐      ┌─────────────┐
     │  process_digest  │─────▶│  SQLite DB   │
     │  (orchestrator)  │      │  (storage)   │
     └────────┬─────────┘      └─────────────┘
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
 Topic     Author    Engagement
 Matching  Tracking  Detection
    │         │          │
    └─────────┼──────────┘
              ▼
     knos-digest/YYYY-MM-DD.md
              │
              ▼
     WhatsApp delivery (2 PM)
```

---

## Quick Start

```bash
# Run full digest pipeline
bash run_digest_v2.sh

# Run tests (82 tests)
venv/bin/python -m pytest tests/ -v

# Sync read items from a digest file
venv/bin/python sync_reading_log.py knos-digest/2026-02-27.md

# Generate engagement summary
venv/bin/python engagement_summary.py

# Run local dashboard
venv/bin/python -m streamlit run dashboard.py
```

---

## Sources

| Source | Fetcher | Config Key | Marker |
|--------|---------|------------|--------|
| Hacker News | `fetch_stories.py` (API) | `sources.hackernews` | (none) |
| Substack | `fetch_substack.py` (RSS) | `sources.substack.feeds` | 📰 |

Stories from all sources share a uniform schema (`id`, `title`, `url`, `score`, `by`, `time`, `descendants`, `text`, `source`) and go through the same semantic matching pipeline.

---

## Digest Format

Each story and engagement opportunity has an inline checkbox for read tracking. Mark `[x]` and add notes directly below any item, then run `sync_reading_log.py` to record to the DB.

```
🦅 *HN Digest* - Afternoon Energy Boost
_4 stories worth your attention_

*AI/ML/LLMs*
- [ ] Nano Banana 2: Google's latest AI image generation model
  ↑533 | 502 comments | by davidbarker
  💬 Discussing: images, image, models
  🔗 https://news.ycombinator.com/item?id=47167858
  Notes:
- [ ] 📰 How to Sound Like an Expert in Any AI Bubble Debate
  ↑0 | 0 comments | by Derek Thompson
  🔗 https://www.derekthompson.org/p/how-to-sound-like-an-expert-in-any
  Notes:

🎯 *Engagement Opportunities*

- [ ] 💬 Show HN: Terminal Phone – E2EE Walkie Talkie
  → Someone built something. 73 comments. Feedback or insights?
  🔗 https://news.ycombinator.com/item?id=47164270
  Notes:

- [ ] 🔥 Statement from Dario Amodei on Department of War
  → Active debate (754 comments). Provide clarity or mental model?
  🔗 https://news.ycombinator.com/item?id=47173121
  Notes:

_Keep building. The frontier moves forward._
```

---

## Pipeline Components

### Fetching
- **`fetch_stories.py`** — HN top stories API, concurrent requests, filters by score (default 50+)
- **`fetch_substack.py`** — RSS feeds via `feedparser`, config-driven feed list, stable IDs from URL hash

### Matching (`match_topics.py`)
- Sentence-transformer embeddings (`all-MiniLM-L6-v2`)
- Topics defined in `config.json` with keyword lists and weights
- Configurable similarity threshold (default 0.3)

### Engagement Detection (`engagement.py`)
- **Ask/Show HN** — explicit feedback requests (score 0.75+)
- **Early threads** — <10 comments, <6h old (score 0.55+)
- **Hot debates** — 50+ comments, active (score 0.45+)
- Comment analysis with question/debate scoring boosts
- Auto-syncs `vb7132`'s HN comments to track engagement

### Storage (`storage_sqlite.py`)
- SQLite via abstract `StorageInterface` (swappable to Postgres)
- Tables: `users`, `topics`, `items`, `item_topic_scores`, `authors`, `digests`, `feedback`, `engagement_opportunities`, `user_comments`, `engagement_stats`

### Read Tracking (`sync_reading_log.py`)
- Parses checked `[x]` items from digest markdown files
- Collects multi-line notes below each item
- Strips emoji prefixes (📰, 💬, 🔥, 🎯) to match titles in DB
- Records `read` or `read_with_note` feedback

### Delivery
- **`send_digest.py`** — WhatsApp via OpenClaw gateway
- **`run_digest_v2.sh`** — full pipeline: fetch all sources, merge, process, archive
- **`daily_digest.sh`** — cron wrapper (2 PM)
- **`engagement_summary.py`** — morning reflection (9 AM)

### Dashboard (`dashboard.py`)
Local Streamlit app for visibility into pipeline state, config management, and ad-hoc queries.

```bash
venv/bin/python -m streamlit run dashboard.py
```

Five tabs:
- **Overview** — item counts by source, digest history, items-by-topic bar chart, engagement stats
- **Config** — edit topics (keywords, weights), sources (feeds, toggles), and pipeline settings; writes directly to `config.json`
- **Stories** — filter items by source, date, score, topic, and author; expandable topic scores per row
- **Authors** — sortable author table with topic affinity tags
- **Simulator** — paste a URL or text, run it through the topic matcher, preview how it would appear in a digest

---

## Configuration (`config.json`)

```json
{
  "sources": {
    "hackernews": { "enabled": true },
    "substack": {
      "enabled": true,
      "feeds": ["https://derekthompson.substack.com/feed"],
      "max_items": 10
    }
  },
  "topics": [
    { "name": "AI/ML/LLMs", "keywords": ["..."], "weight": 1.0 },
    { "name": "Data Science", "keywords": ["..."], "weight": 1.0 }
  ],
  "storage": {
    "backend": "sqlite",
    "sqlite": { "db_path": "hn_digest_v2.db" }
  },
  "settings": {
    "max_stories": 30,
    "min_score": 50,
    "similarity_threshold": 0.3,
    "notable_author_threshold": 3
  }
}
```

---

## File Structure

```
knowledge-os/
├── config.json                  # Topics, sources, settings (gitignored)
├── config.example.json          # Template config
│
├── Pipeline
│   ├── fetch_stories.py         # HN API fetcher
│   ├── fetch_substack.py        # Substack RSS fetcher
│   ├── match_topics.py          # Semantic topic matcher
│   ├── process_digest.py        # Main orchestration + digest formatting
│   ├── engagement.py            # Engagement detection + comment tracking
│   └── sync_reading_log.py      # Parse read items from digest markdown
│
├── Storage
│   ├── storage_interface.py     # Abstract base class
│   ├── storage_sqlite.py        # SQLite implementation
│   └── hn_digest_v2.db          # Database (gitignored)
│
├── Delivery
│   ├── run_digest_v2.sh         # Full pipeline script
│   ├── daily_digest.sh          # Cron wrapper (2 PM digest)
│   ├── send_digest.py           # WhatsApp sender
│   ├── engagement_summary.py    # Morning summary generator
│   └── send_engagement_summary.sh
│
├── Tests (82 tests)
│   ├── tests/test_process_digest.py
│   ├── tests/test_storage.py
│   ├── tests/test_engagement.py
│   ├── tests/test_sync_reading_log.py
│   ├── tests/test_fetch_substack.py
│   └── tests/test_pipeline_integration.py
│
├── Output
│   ├── knos-digest/YYYY-MM-DD.md   # Daily digest archive
│   └── archive/                     # Legacy archive
│
└── Docs
    ├── NEXT.md                  # Roadmap
    ├── CLAUDE.md                # AI assistant instructions
    ├── ARCHITECTURE.md
    ├── DAILY_FLOW.md
    └── ENGAGEMENT.md
```

---

## Scheduling

```bash
# Digest: 2 PM daily
0 14 * * * /Users/vb/.openclaw/workspace/knowledge-os/daily_digest.sh

# Engagement summary: 9 AM daily
0 9 * * * /Users/vb/.openclaw/workspace/knowledge-os/send_engagement_summary.sh
```

---

## Tech Stack

- **Python 3.11** with `venv/` (packages via `uv`)
- **sentence-transformers** (`all-MiniLM-L6-v2`) for semantic matching
- **feedparser** for Substack RSS
- **SQLite 3** for storage
- **HN Firebase API** for story fetching
- **OpenClaw** for WhatsApp delivery
- **pytest** for testing (82 tests, `tmp_path` fixtures)

---

## Recent Updates

**2026-02-27:** Multi-source support, inline read tracking, integration tests
- Substack RSS fetcher with config-driven feeds and 📰 source indicator
- Inline checkboxes + notes on every story and engagement item (removed separate Read Tracker section)
- Pipeline integration test (end-to-end with mocked externals)
- Fixed `run_digest_v2.sh` to use `venv/bin/python`

**2026-02-20:** Engagement detection + digest archive
- 5 opportunities/day (Ask/Show HN, early threads, debates)
- Username tracking (vb7132) with auto comment sync
- `knos-digest/YYYY-MM-DD.md` archive format

**2026-02-13:** Storage v2 architecture
- SQLite backend with abstract interface
- Author tracking, digest history, feedback logging

**2026-02-11:** Initial launch
- Semantic topic matching, daily WhatsApp delivery

---

See [NEXT.md](NEXT.md) for the roadmap.

_Built with OpenClaw by Crow_
