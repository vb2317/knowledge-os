"""Tests for process_digest.py pure functions"""
import pytest
from datetime import datetime, timedelta
from process_digest import (
    _extract_first_sentence,
    _extract_keywords,
    _filter_by_age,
    summarize_comments,
    generate_digest_text,
)


# --- _extract_first_sentence ---

class TestExtractFirstSentence:
    def test_plain_sentence(self):
        assert _extract_first_sentence("Hello world. More text here.") == "Hello world."

    def test_html_tags_stripped(self):
        result = _extract_first_sentence("<p>Hello <b>world</b>. More.</p>")
        assert "<" not in result
        assert "Hello" in result

    def test_html_entities_decoded(self):
        result = _extract_first_sentence("A &amp; B are great. Next.")
        assert result == "A & B are great."

    def test_empty_string(self):
        assert _extract_first_sentence("") == ""

    def test_no_sentence_boundary(self):
        text = "This is a comment without ending punctuation"
        result = _extract_first_sentence(text)
        assert result == text

    def test_long_text_truncated(self):
        text = "A" * 200
        result = _extract_first_sentence(text)
        assert len(result) <= 120

    def test_exclamation_boundary(self):
        assert _extract_first_sentence("Wow! That's great.") == "Wow!"

    def test_question_boundary(self):
        assert _extract_first_sentence("Really? I doubt it.") == "Really?"


# --- _extract_keywords ---

class TestExtractKeywords:
    def test_basic_extraction(self):
        sentences = ["Rust programming language", "Rust compiler performance"]
        stop_words = {"this", "that", "with"}
        result = _extract_keywords(sentences, stop_words)
        assert "rust" in result

    def test_stop_words_filtered(self):
        sentences = ["This is about using things really well"]
        stop_words = {"this", "about", "using", "things", "really", "well"}
        result = _extract_keywords(sentences, stop_words)
        assert "this" not in result
        assert "about" not in result

    def test_short_words_ignored(self):
        """Words shorter than 4 chars are excluded by the regex"""
        sentences = ["Go is a fun and new language"]
        result = _extract_keywords(sentences, set())
        assert "fun" not in result  # 3 chars
        assert "language" in result

    def test_empty_input(self):
        assert _extract_keywords([], set()) == []

    def test_returns_max_five(self):
        sentences = ["alpha bravo charlie delta echo foxtrot golf hotel india juliet"]
        result = _extract_keywords(sentences, set())
        assert len(result) <= 5

    def test_frequency_ordering(self):
        sentences = ["python python python", "python rust rust", "rust golang"]
        result = _extract_keywords(sentences, set())
        assert result[0] == "python"


# --- _filter_by_age ---

class TestFilterByAge:
    def _story(self, published_at):
        return {"title": "T", "published_at": published_at}

    def test_recent_story_passes(self):
        s = self._story(datetime.now().isoformat())
        assert _filter_by_age([s], 7) == [s]

    def test_old_story_filtered(self):
        s = self._story("2020-01-01T00:00:00")
        assert _filter_by_age([s], 7) == []

    def test_no_published_at_passes(self):
        s = {"title": "no date"}
        assert _filter_by_age([s], 7) == [s]

    def test_empty_published_at_passes(self):
        s = self._story("")
        assert _filter_by_age([s], 7) == [s]

    def test_invalid_date_passes(self):
        s = self._story("not-a-date")
        assert _filter_by_age([s], 7) == [s]

    def test_within_boundary_passes(self):
        s = self._story((datetime.now() - timedelta(days=6)).isoformat())
        assert _filter_by_age([s], 7) == [s]

    def test_outside_boundary_filtered(self):
        s = self._story((datetime.now() - timedelta(days=8)).isoformat())
        assert _filter_by_age([s], 7) == []

    def test_mixed_keeps_only_recent(self):
        recent = self._story(datetime.now().isoformat())
        old = self._story("2020-01-01T00:00:00")
        no_date = {"title": "no date"}
        result = _filter_by_age([recent, old, no_date], 7)
        assert result == [recent, no_date]

    def test_empty_list(self):
        assert _filter_by_age([], 7) == []


# --- summarize_comments ---

class TestSummarizeComments:
    def test_empty_comments(self):
        assert summarize_comments([]) is None

    def test_empty_comments_with_descendants(self):
        assert summarize_comments([], descendants=42) == "42 comments"

    def test_comments_with_text(self):
        comments = [
            {"text": "<p>Python performance is impressive. Very cool.</p>"},
            {"text": "<p>Python async support matters. Great work.</p>"},
            {"text": "<p>The python ecosystem keeps growing. Nice.</p>"},
        ]
        result = summarize_comments(comments)
        assert result is not None
        assert "Discussing:" in result

    def test_comments_no_text(self):
        comments = [{"text": ""}, {"text": ""}]
        result = summarize_comments(comments, descendants=10)
        assert result == "10 comments"

    def test_comments_no_keywords_fallback(self):
        # Very short words that won't match 4+ char regex
        comments = [{"text": "ok lol yes no"}]
        result = summarize_comments(comments, descendants=5)
        assert result == "5 comments"


# --- generate_digest_text ---

class TestGenerateDigestText:
    def _make_story(self, title="Test Story", score=100, topic="AI/ML", **kwargs):
        defaults = {
            "title": title,
            "score": score,
            "matched_topic": topic,
            "by": "testuser",
            "id": 12345,
            "url": "https://example.com",
            "descendants": 50,
            "all_topic_scores": {topic: 0.9},
            "comment_summary": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_empty_stories(self):
        result = generate_digest_text({"stories": [], "notable_authors": []})
        assert "Quiet day" in result

    def test_basic_digest_format(self):
        story = self._make_story()
        result = generate_digest_text({
            "stories": [story],
            "notable_authors": [],
            "engagement_opportunities": [],
        })
        assert "HN Digest" in result
        assert "Test Story" in result
        assert "↑100" in result
        assert "https://news.ycombinator.com/item?id=12345" in result

    def test_comment_summary_included(self):
        story = self._make_story(comment_summary="Discussing: rust, wasm, perf")
        result = generate_digest_text({
            "stories": [story],
            "notable_authors": [],
            "engagement_opportunities": [],
        })
        assert "Discussing: rust, wasm, perf" in result

    def test_notable_author_star(self):
        story = self._make_story(by="notable_dev")
        result = generate_digest_text({
            "stories": [story],
            "notable_authors": [
                {"author_name": "notable_dev", "story_count": 5, "topics": {"AI/ML": 0.9}}
            ],
            "engagement_opportunities": [],
        })
        assert "⭐" in result

    def test_inline_checkbox_on_stories(self):
        story = self._make_story()
        result = generate_digest_text({
            "stories": [story],
            "notable_authors": [],
            "engagement_opportunities": [],
        })
        assert "- [ ] Test Story" in result
        assert "  Notes: " in result
        # No separate read tracker section
        assert "## 📖 Read Tracker" not in result

    def test_no_separate_read_tracker(self):
        story = self._make_story(title="Main Story")
        eng_story = self._make_story(title="Engagement Story", id=99999)
        result = generate_digest_text({
            "stories": [story],
            "notable_authors": [],
            "engagement_opportunities": [{"story": eng_story, "type": "early",
                                          "score": 0.8, "action_prompt": "Go!"}],
        })
        assert "- [ ] Main Story" in result
        assert "## 📖 Read Tracker" not in result

    def test_multiple_topics_grouped(self):
        s1 = self._make_story(title="AI thing", topic="AI/ML")
        s2 = self._make_story(title="Rust thing", topic="Systems", id=99999,
                              url="https://example.com/2")
        result = generate_digest_text({
            "stories": [s1, s2],
            "notable_authors": [],
            "engagement_opportunities": [],
        })
        assert "*AI/ML*" in result
        assert "*Systems*" in result
