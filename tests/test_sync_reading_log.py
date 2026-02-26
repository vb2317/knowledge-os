"""Tests for sync_reading_log.py"""
import pytest
from sync_reading_log import parse_read_items


SAMPLE_DIGEST = """\
🦅 *HN Digest* - Afternoon Energy Boost
_3 stories worth your attention_

*AI/ML*
• Cool AI Tool
  ↑200 | 50 comments | by alice
  🔗 https://news.ycombinator.com/item?id=1

*Systems*
• Rust is Fast
  ↑150 | 30 comments | by bob
  🔗 https://news.ycombinator.com/item?id=2

_Keep building. The frontier moves forward._

---
## 📖 Read Tracker
_Mark what you read, add notes if you like_

- [x] Cool AI Tool (↑200)
  Notes: Really impressive demo
- [ ] Rust is Fast (↑150)
  Notes:
- [x] Show HN: My Project (↑80)
  Notes:
"""


class TestParseReadItems:
    def test_finds_checked_items(self):
        items = parse_read_items(SAMPLE_DIGEST)
        assert len(items) == 2

    def test_extracts_titles(self):
        items = parse_read_items(SAMPLE_DIGEST)
        titles = [i["title"] for i in items]
        assert "Cool AI Tool" in titles
        assert "Show HN: My Project" in titles

    def test_extracts_scores(self):
        items = parse_read_items(SAMPLE_DIGEST)
        by_title = {i["title"]: i for i in items}
        assert by_title["Cool AI Tool"]["score"] == 200
        assert by_title["Show HN: My Project"]["score"] == 80

    def test_extracts_notes(self):
        items = parse_read_items(SAMPLE_DIGEST)
        by_title = {i["title"]: i for i in items}
        assert by_title["Cool AI Tool"]["note"] == "Really impressive demo"
        assert by_title["Show HN: My Project"]["note"] == ""

    def test_unchecked_items_skipped(self):
        items = parse_read_items(SAMPLE_DIGEST)
        titles = [i["title"] for i in items]
        assert "Rust is Fast" not in titles

    def test_no_tracker_section(self):
        md = "# Just a heading\nSome text\n"
        assert parse_read_items(md) == []

    def test_empty_input(self):
        assert parse_read_items("") == []

    def test_case_insensitive_checkbox(self):
        md = "- [X] Title Here (↑42)\n  Notes: \n"
        items = parse_read_items(md)
        assert len(items) == 1
        assert items[0]["title"] == "Title Here"
