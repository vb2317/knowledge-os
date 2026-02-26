# knowledge-os

HN digest pipeline that fetches stories, matches to user topics via semantic similarity, detects engagement opportunities, and delivers daily digests.

## Commands

```bash
# Run full digest pipeline
bash run_digest_v2.sh

# Run tests
venv/bin/python -m pytest tests/ -v

# Sync reading log from a digest file
venv/bin/python sync_reading_log.py knos-digest/YYYY-MM-DD.md

# Run engagement summary
venv/bin/python engagement_summary.py
```

## Environment

- **Package manager:** Always use `uv` — never bare `pip` or `pip3`
  - Install: `uv pip install <pkg> --python venv/bin/python`
- **Python:** Always use `venv/bin/python`, never system python
- **Database:** SQLite at `hn_digest_v2.db` — never DROP or DELETE without WHERE
- **Tests:** pytest with `tmp_path` fixtures for DB isolation (not `:memory:` — connections don't persist across `_get_conn()` calls)

## Architecture

```
fetch_stories.py → process_digest.py → knos-digest/YYYY-MM-DD.md
                        ↓
                  storage_sqlite.py (SQLite via storage_interface.py ABC)
                        ↓
                  engagement.py (opportunity detection, comment sync)
```

- `config.json` — single source for topics, user, storage config, thresholds
- `storage_interface.py` — abstract base; `storage_sqlite.py` implements it
- `match_topics.py` — sentence-transformers semantic matching (heavy import, avoid in tests)

## Code Conventions

- Config loading: use `load_config()` from `process_digest.py` or inline `json.load(open("config.json"))`
- DB access in production code: go through `storage_interface.get_storage()` factory
- DB access in `engagement.py`: uses raw `sqlite3` directly (separate schema)
- Errors/warnings: `print(..., file=sys.stderr)` — stdout is reserved for pipeline output
- Archive naming: `archive/YYYY-MM-DD_{stories,digest}.{json,txt}`, digest markdown in `knos-digest/YYYY-MM-DD.md`
- HN username `vb7132` is hardcoded in `engagement.py` and `engagement_summary.py`

## Testing

- All tests in `tests/` — run with `venv/bin/python -m pytest tests/ -v`
- Use `tmp_path` fixture for SQLite (not `:memory:`)
- Don't import `match_topics` or `sentence_transformers` in tests — they load heavy ML models
- Test pure functions directly; mock network calls
