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

# Fetch and store only (no digest generation — for 6-hour cron)
bash run_digest_v2.sh --fetch-only

# Run tests (131 tests; integration tests require DB and are excluded in CI)
venv/bin/python -m pytest tests/ -v -m "not integration"

# Sync read items from a digest file
venv/bin/python sync_reading_log.py knos-digest/YYYY-MM-DD.md

# Weekly trending topics summary
venv/bin/python weekly_summary.py

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

Stories from all sources share a uniform schema (`id`, `title`, `url`, `score`, `by`, `time`, `descendants`, `text`, `source`, `published_at`) and go through the same semantic matching pipeline.

---

## Digest Format

Each story and engagement opportunity has an inline checkbox for read tracking. Mark `[x]` and add notes directly below any item, then run `sync_reading_log.py` to record to the DB.

Weekday digest — topic-grouped:
```
🦅 *HN Digest* - Afternoon Energy Boost
_4 stories worth your attention_

*AI/ML/LLMs*
- [ ] Nano Banana 2: Google's latest AI image generation model
  ↑533 | karma: 14,821 | by davidbarker
  💬 This is a significant step forward in diffusion-based generation.
  🔗 https://news.ycombinator.com/item?id=47167858
  Notes:
- [ ] 📰 How to Sound Like an Expert in Any AI Bubble Debate
  ↑0 | karma: 3,204 | by Derek Thompson
  🔗 https://www.derekthompson.org/p/how-to-sound-like-an-expert-in-any
  Notes:

_Keep building. The frontier moves forward._
```

Weekend digest — engagement-sorted:
```
🌿 *Weekend Reads* — Sat, Mar 7
_2 top matches · 10 interesting reads_

── Best Matches ──────────────────────
- [ ] Story matching your topics above the weekend threshold
  ↑480 | karma: 9,102 | by author
  🔗 https://news.ycombinator.com/item?id=...
  Notes:

── Interesting Reads ─────────────────
- [ ] Global warming has accelerated significantly
  ↑1057 | karma: 4,211 | by morsch
  💬 The methodology section is worth reading carefully.
  🔗 https://news.ycombinator.com/item?id=47275088
  Notes:

_A quieter read for the weekend._
```

---

## Pipeline Components

### Fetching
- **`fetch_stories.py`** — HN top stories API, concurrent requests, filters by score (default 50+)
- **`fetch_substack.py`** — RSS feeds via `feedparser`, config-driven feed list, stable IDs from URL hash; feeds accept per-feed `frequency` overrides as `{"url": "...", "frequency": "weekly"}` dicts

### Matching (`match_topics.py`)
- Sentence-transformer embeddings (`all-MiniLM-L6-v2`)
- Topics defined in `config.json` with keyword lists and weights
- Configurable similarity threshold (default 0.3)
- `score_all_stories()` — scores all fetched stories without threshold filtering (used by weekend mode for the Interesting Reads pool)

### Engagement Detection (`engagement.py`)
- **Ask/Show HN** — explicit feedback requests (score 0.75+)
- **Early threads** — <10 comments, <6h old (score 0.55+)
- **Hot debates** — 50+ comments, active (score 0.45+)
- Comment analysis with question/debate scoring boosts
- Auto-syncs `vb7132`'s HN comments to track engagement
- `fetch_user_karma(username)` — fetches HN karma per author for digest display

### Storage (`storage_sqlite.py`)
- SQLite via abstract `StorageInterface` (swappable to Postgres)
- Tables: `users`, `topics`, `items`, `item_topic_scores`, `authors`, `digests`, `feedback`, `engagement_opportunities`, `user_comments`, `engagement_stats`
- `items.published_at` (ISO 8601) tracks original publication date; on re-fetch, if `published_at` is newer than stored, the item re-surfaces in the digest

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

Six tabs:
- **Overview** — item counts by source, digest history, items-by-topic bar chart, engagement stats
- **Browse** — browse all stored stories by publication date with topic, source, and date-range filters; card layout with direct links
- **Config** — edit topics (keywords, weights), sources (feeds, toggles), pipeline settings, weekend mode, and followed HN users; writes directly to `config.json`
- **Stories** — filter items by source, date, score, topic, and author; expandable topic scores per row
- **Authors** — sortable author table with topic affinity tags
- **Simulator** — paste a URL or text, run it through the topic matcher, preview how it would appear in a digest

---

## Configuration (`config.json`)

The `frequency` field on each source controls which days its stories surface in the digest. All sources are still fetched and stored daily for tracking — frequency only affects digest inclusion.

Valid values: `"daily"` (default), `"weekly"` (Mondays), `"biweekly"` (Mondays of even ISO weeks), `"monthly"` (1st of month), `"quarterly"` (Jan/Apr/Jul/Oct 1st), or a list like `["mon", "wed", "fri"]`.

Substack feeds also accept per-feed frequency overrides as objects:
```json
"feeds": [
  "https://derekthompson.substack.com/feed",
  { "url": "https://stateoverflow.substack.com/feed", "frequency": "weekly" }
]
```

Full config shape:
```json
{
  "sources": {
    "hackernews": { "enabled": true, "frequency": "daily" },
    "substack": {
      "enabled": true,
      "frequency": "daily",
      "feeds": ["https://derekthompson.substack.com/feed"],
      "max_items": 10
    }
  },
  "topics": [
    { "name": "AI/ML/LLMs", "keywords": ["..."], "weight": 1.0 }
  ],
  "storage": {
    "backend": "sqlite",
    "sqlite": { "db_path": "hn_digest_v2.db" }
  },
  "settings": {
    "max_stories": 30,
    "min_score": 50,
    "max_age_days": 7,
    "similarity_threshold": 0.3,
    "notable_author_threshold": 3,
    "followed_hn_users": ["pg", "dang"],
    "weekend_mode": {
      "enabled": true,
      "apply_on": ["sat", "sun"],
      "similarity_threshold": 0.45,
      "max_top_matches": 10,
      "interesting_reads_count": 10,
      "interesting_min_score": 100,
      "digest_title": "Weekend Reads"
    }
  }
}
```

---

## File Structure

```
knowledge-os/
├── config.json                  # Topics, sources, settings (gitignored)
├── config.example.json          # Template config
├── pytest.ini                   # pytest marker definitions
│
├── Pipeline
│   ├── fetch_stories.py         # HN API fetcher
│   ├── fetch_substack.py        # Substack RSS fetcher (per-feed frequency)
│   ├── match_topics.py          # Semantic topic matcher + score_all_stories()
│   ├── process_digest.py        # Main orchestration, digest formatting, weekend mode
│   ├── engagement.py            # Engagement detection, comment tracking, karma fetch
│   ├── sync_reading_log.py      # Parse read items from digest markdown
│   └── weekly_summary.py        # Weekly trending topics report
│
├── Storage
│   ├── storage_interface.py     # Abstract base class
│   ├── storage_sqlite.py        # SQLite implementation
│   └── hn_digest_v2.db          # Database (gitignored)
│
├── Delivery
│   ├── run_digest_v2.sh         # Full pipeline (--fetch-only for 6h cron)
│   ├── daily_digest.sh          # Cron wrapper (2 PM digest)
│   ├── send_digest.py           # WhatsApp sender
│   ├── engagement_summary.py    # Morning summary generator
│   └── send_engagement_summary.sh
│
├── CI
│   └── .github/workflows/tests.yml  # GitHub Actions — unit tests on push/PR
│
├── Tests (131 tests)
│   ├── tests/test_process_digest.py       # unit
│   ├── tests/test_storage.py              # unit
│   ├── tests/test_engagement.py           # unit
│   ├── tests/test_sync_reading_log.py     # unit
│   ├── tests/test_fetch_substack.py       # unit
│   └── tests/test_pipeline_integration.py # integration (marked, excluded from CI)
│
├── Output
│   ├── knos-digest/YYYY-MM-DD.md   # Daily digest archive
│   └── archive/                     # Raw story/digest archive
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

# Fetch-only: every 6 hours (keeps DB fresh for weekend mode Interesting Reads)
0 */6 * * * bash /Users/vb/.openclaw/workspace/knowledge-os/run_digest_v2.sh --fetch-only

# Weekly summary: Monday 9 AM
0 9 * * 1 /Users/vb/.openclaw/workspace/knowledge-os/venv/bin/python /Users/vb/.openclaw/workspace/knowledge-os/weekly_summary.py

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
- **pytest** for testing (131 tests, `tmp_path` fixtures, `integration` marker)

---

## Recent Updates

**2026-03-07:** Weekend mode, karma display, followed users, CI, weekly summary
- **Weekend mode** — Saturday/Sunday digest splits into "Best Matches" (stricter threshold) and "Interesting Reads" (high-HN-score stories regardless of topic); fully configurable via dashboard Config tab
- **Digest format** — comment count replaced with author HN karma (`karma: N`); top comment's first sentence shown as 💬 blurb instead of keyword extraction
- **Followed HN users** — `followed_hn_users` config list; followed users get ⭐ in digest regardless of story count; add/remove via dashboard
- **Per-feed Substack frequency** — individual feeds can override the source-level frequency with `{"url": "...", "frequency": "weekly"}`
- **Weekly summary** — `weekly_summary.py` reports last 7 days of matched stories by topic
- **GitHub Actions CI** — `.github/workflows/tests.yml` runs unit tests on push/PR; integration tests marked and excluded
- **`run_digest_v2.sh --fetch-only`** — fetches and stores without generating a digest (for 6-hour cron)

**2026-03-03:** published_at tracking, 52 Substack feeds, Browse tab, age filter
- All stories now carry `published_at` (ISO 8601); HN from `time` field, Substack from `updated_parsed` or `published_parsed`
- `storage_sqlite.py`: if a re-fetched URL has a newer `published_at`, record is updated and story re-surfaces in the digest
- `max_age_days` config setting (default 7) filters stories before matching — prevents old Substack backlog from flooding the digest
- 52 Substack feeds added from TSPC community CSV
- Dashboard **Browse** tab: card-based reading view, filter by topic/source/date range, grouped by publication date

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
