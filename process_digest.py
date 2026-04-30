#!/usr/bin/env python3
"""
Main digest processing pipeline using new storage architecture
"""
import json
import re
import sys
from datetime import datetime
from typing import List, Dict
from storage_interface import get_storage
from match_topics import TopicMatcher

# Import engagement detection
try:
    from engagement import EngagementDetector, format_engagement_section
    ENGAGEMENT_ENABLED = True
except ImportError:
    ENGAGEMENT_ENABLED = False
    print("Warning: Engagement module not available", file=sys.stderr)

def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration"""
    with open(config_path) as f:
        return json.load(f)

def _extract_first_sentence(html_text: str) -> str:
    """Extract first meaningful sentence from an HN comment (HTML)."""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_text)
    # Decode common HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#x27;', "'").replace('&quot;', '"')
    text = text.strip()
    if not text:
        return ""
    # Take first sentence (split on . ! ?)
    match = re.match(r'(.+?[.!?])\s', text)
    if match:
        return match.group(1).strip()
    # Fallback: first 120 chars
    return text[:120].strip()


def _extract_keywords(sentences: List[str], stop_words: set) -> List[str]:
    """Extract key topic words from sentences."""
    word_counts = {}
    for sent in sentences:
        words = re.findall(r'[a-zA-Z]{4,}', sent.lower())
        for w in words:
            if w not in stop_words:
                word_counts[w] = word_counts.get(w, 0) + 1
    # Return top words by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:5]]


def summarize_comments(comments: List[Dict], descendants: int = 0) -> str:
    """Return the first sentence of the top HN comment, or a fallback string."""
    if not comments:
        return f"{descendants} comments" if descendants else None

    text = comments[0].get('text', '')
    if text:
        sent = _extract_first_sentence(text)
        if sent:
            return sent

    return f"{descendants} comments" if descendants else None


_WEEKDAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _source_is_due(frequency, today: datetime = None) -> bool:
    """Return True if this source should surface in today's digest."""
    if today is None:
        today = datetime.now()
    if not frequency or frequency == "daily":
        return True
    if isinstance(frequency, list):
        day_name = _WEEKDAY_NAMES[today.weekday()]
        return day_name in [d.lower()[:3] for d in frequency]
    freq = frequency.lower()
    if freq == "weekly":
        return today.weekday() == 0  # Monday
    if freq == "biweekly":
        return today.weekday() == 0 and today.isocalendar()[1] % 2 == 0
    if freq == "monthly":
        return today.day == 1
    if freq == "quarterly":
        return today.day == 1 and today.month in (1, 4, 7, 10)
    return True  # unknown frequency → always include


def _is_weekend(today: datetime = None) -> bool:
    """Return True if today is Saturday or Sunday."""
    if today is None:
        today = datetime.now()
    return today.weekday() in (5, 6)


def _apply_weekend_mode(scored_stories, config, today=None):
    """
    Split stories into (top_matches, interesting_reads) for weekend digest.
    - top_matches: stories whose max topic similarity >= weekend threshold, sorted by HN score
    - interesting_reads: remaining stories with HN score >= interesting_min_score, sorted by score
    """
    wm = config.get("settings", {}).get("weekend_mode", {})
    threshold = float(wm.get("similarity_threshold", 0.45))
    max_top = int(wm.get("max_top_matches", 10))
    interesting_count = int(wm.get("interesting_reads_count", 10))
    interesting_min_score = int(wm.get("interesting_min_score", 100))

    top_matches = [s for s, sim in scored_stories if sim >= threshold]
    top_matches = sorted(top_matches, key=lambda s: s.get("score", 0), reverse=True)[:max_top]
    top_match_urls = {s["url"] for s in top_matches}

    interesting = [
        s for s, _ in scored_stories
        if s["url"] not in top_match_urls and s.get("score", 0) >= interesting_min_score
    ]
    interesting = sorted(interesting, key=lambda s: s.get("score", 0), reverse=True)[:interesting_count]

    return top_matches, interesting


def _filter_by_age(stories: List[Dict], max_age_days: int) -> List[Dict]:
    """Return only stories whose published_at is within max_age_days of now.
    Stories with missing or unparseable published_at are kept."""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=max_age_days)
    result = []
    for story in stories:
        pub = story.get('published_at', '')
        if not pub:
            result.append(story)
            continue
        try:
            if datetime.fromisoformat(pub) >= cutoff:
                result.append(story)
        except ValueError:
            result.append(story)
    return result


def process_stories(stories: List[Dict], config: Dict) -> Dict:
    """Process stories through the new storage pipeline"""
    import time

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing {len(stories)} stories...", file=sys.stderr)
    start_time = time.time()

    # Drop stories older than max_age_days
    max_age_days = config['settings'].get('max_age_days', 7)
    before = len(stories)
    stories = _filter_by_age(stories, max_age_days)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Age filter ({max_age_days}d): {before} → {len(stories)} stories", file=sys.stderr)

    # Filter stories by source frequency
    sources_cfg = config.get('sources', {})
    before = len(stories)
    stories = [
        s for s in stories
        if _source_is_due(
            sources_cfg.get(s.get('source', 'hackernews'), {}).get('frequency', 'daily')
        )
    ]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Frequency filter: {before} → {len(stories)} stories", file=sys.stderr)

    # Initialize storage
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing storage...", file=sys.stderr)
    storage_start = time.time()
    storage_config = config['storage']
    storage = get_storage(
        backend=storage_config['backend'],
        **storage_config.get(storage_config['backend'], {})
    )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Storage initialized in {time.time() - storage_start:.1f}s", file=sys.stderr)
    
    # Get or create user
    user_start = time.time()
    user_id = storage.get_or_create_user(
        identifier=config['user']['identifier']
    )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] User loaded in {time.time() - user_start:.1f}s", file=sys.stderr)
    
    # Initialize topics if needed
    topics_start = time.time()
    existing_topics = storage.get_topics(user_id)
    if not existing_topics:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Creating topics...", file=sys.stderr)
        for topic in config['topics']:
            storage.insert_topic(
                user_id=user_id,
                name=topic['name'],
                keywords=topic['keywords'],
                weight=topic.get('weight', 1.0)
            )
        existing_topics = storage.get_topics(user_id)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Topics loaded in {time.time() - topics_start:.1f}s ({len(existing_topics)} topics)", file=sys.stderr)
    
    # Match topics using existing matcher
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting topic matching (embeddings)...", file=sys.stderr)
    matcher_start = time.time()
    matcher = TopicMatcher(config=config)
    matched_stories = matcher.match_stories(stories)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Topic matching completed in {time.time() - matcher_start:.1f}s ({len(matched_stories)} matched)", file=sys.stderr)

    # Score all stories for weekend mode (no threshold filter — needed for Interesting Reads pool)
    wm_cfg = config.get("settings", {}).get("weekend_mode", {})
    all_scored_stories = None
    if wm_cfg.get("enabled"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scoring all stories for weekend mode...", file=sys.stderr)
        all_scored_stories = matcher.score_all_stories(stories)
    
    weekend_mode_active = wm_cfg.get("enabled") and _is_weekend()
    stories_to_store = matched_stories
    if weekend_mode_active and all_scored_stories is not None:
        stories_to_store = [story for story, _ in all_scored_stories]

    # Process each story
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Storing {len(stories_to_store)} stories in database...", file=sys.stderr)
    db_start = time.time()
    item_ids = []
    new_story_urls = set()
    notable_authors = []
    continuing_threads = []

    for story in stories_to_store:
        # Insert item — is_new=False means already delivered in a prior digest
        item_id, is_new = storage.insert_item(
            url=story['url'],
            title=story['title'],
            source=story.get('source', 'hackernews'),
            author=story['by'],
            score=story['score'],
            fetched_at=story['fetched_at'],
            published_at=story.get('published_at', ''),
            external_id=str(story['id']) if story.get('id') is not None else None,
        )

        # Store topic scores and author stats for all stories (tracking still applies)
        for topic in existing_topics:
            if topic['name'] in story['all_topic_scores']:
                score = story['all_topic_scores'][topic['name']]
                storage.insert_item_topic_score(
                    item_id=item_id,
                    topic_id=topic['topic_id'],
                    score=score
                )

        storage.upsert_author(
            user_id=user_id,
            author_name=story['by'],
            item_id=item_id,
            topic_scores=story['all_topic_scores']
        )

        # Only surface new stories in the digest
        if is_new:
            item_ids.append(item_id)
            new_story_urls.add(story['url'])

    if weekend_mode_active and all_scored_stories is not None:
        all_scored_stories = [
            (story, sim) for story, sim in all_scored_stories
            if story['url'] in new_story_urls
        ]
        display_stories = [story for story, _ in all_scored_stories]
    else:
        display_stories = [story for story in matched_stories if story['url'] in new_story_urls]

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Database storage completed in {time.time() - db_start:.1f}s ({len(display_stories)} new)", file=sys.stderr)
    
    # Get notable authors
    authors_start = time.time()
    notable_authors = storage.get_notable_authors(
        user_id=user_id,
        min_count=config['settings']['notable_author_threshold']
    )
    
    # Filter notable authors that appear in current batch
    current_authors = {s['by'] for s in display_stories}
    batch_notable = [a for a in notable_authors if a['author_name'] in current_authors]

    # Merge manually followed HN users (highlighted regardless of story count)
    followed_users = config.get('settings', {}).get('followed_hn_users', [])
    if followed_users:
        existing_notable_names = {a['author_name'] for a in batch_notable}
        for username in followed_users:
            if username in current_authors and username not in existing_notable_names:
                batch_notable.append({
                    'author_name': username,
                    'story_count': 0,
                    'topics': {},
                })
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Notable authors identified in {time.time() - authors_start:.1f}s ({len(batch_notable)} in batch)", file=sys.stderr)
    
    # Record digest
    digest_start = time.time()
    digest_id = storage.insert_digest(
        user_id=user_id,
        item_ids=item_ids,
        sent_at=datetime.now().isoformat()
    )

    # Log delivered feedback for each item
    for item_id in item_ids:
        storage.insert_feedback(
            user_id=user_id,
            item_id=item_id,
            action='delivered',
            metadata={'digest_id': digest_id}
        )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Digest recorded in {time.time() - digest_start:.1f}s", file=sys.stderr)

    # Fetch comment summaries and author karma for matched stories
    if ENGAGEMENT_ENABLED and display_stories:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching comment summaries and author karma...", file=sys.stderr)
        comments_start = time.time()
        try:
            db_config = config['storage']['sqlite']
            comment_detector = EngagementDetector(db_config['db_path'])
            karma_cache = {}
            for story in display_stories:
                story_id = story.get('id')
                if story_id:
                    try:
                        comments = comment_detector.fetch_story_comments(story_id, max_depth=1)
                        story['comment_summary'] = summarize_comments(comments, story.get('descendants', 0))
                    except Exception:
                        story['comment_summary'] = None
                author = story.get('by', '')
                if author and author not in karma_cache:
                    karma_cache[author] = comment_detector.fetch_user_karma(author)
                story['author_karma'] = karma_cache.get(author)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Comments and karma fetched in {time.time() - comments_start:.1f}s", file=sys.stderr)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Comment/karma fetch failed: {e}", file=sys.stderr)

    # Detect engagement opportunities
    engagement_opportunities = []
    if ENGAGEMENT_ENABLED and display_stories:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Detecting engagement opportunities...", file=sys.stderr)
        engagement_start = time.time()
        try:
            # Get raw stories with HN data for engagement detection
            db_config = config['storage']['sqlite']
            detector = EngagementDetector(db_config['db_path'])
            engagement_opportunities = detector.detect_opportunities(stories, max_results=5)
            detector.save_opportunities(engagement_opportunities, datetime.now().date().isoformat())
            
            # Sync user comments in background
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Syncing user comments...", file=sys.stderr)
            sync_start = time.time()
            detector.sync_user_comments()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] User comments synced in {time.time() - sync_start:.1f}s", file=sys.stderr)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Engagement detection completed in {time.time() - engagement_start:.1f}s", file=sys.stderr)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Engagement detection failed: {e}", file=sys.stderr)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Total processing time: {time.time() - start_time:.1f}s", file=sys.stderr)
    
    return {
        'stories': display_stories,
        'notable_authors': batch_notable,
        'digest_id': digest_id,
        'item_ids': item_ids,
        'engagement_opportunities': engagement_opportunities,
        'all_scored_stories': all_scored_stories,
    }

def _format_story_lines(story, notable_authors):
    """Return a list of lines for a single story entry."""
    lines = []
    title = story['title']
    score = story['score']
    author = story['by']
    story_id = story.get('id')
    descendants = story.get('descendants', 0)
    comment_summary = story.get('comment_summary')

    author_marker = ""
    if notable_authors:
        for notable in notable_authors:
            if notable['author_name'] == author:
                author_marker = " ⭐"
                break

    karma = story.get('author_karma')
    karma_str = f"karma: {karma:,}" if karma is not None else ""
    source_icon = "📰 " if story.get('source') == 'substack' else ""
    lines.append(f"- [ ] {source_icon}{title}")
    meta_parts = [f"↑{score}"]
    if karma_str:
        meta_parts.append(karma_str)
    meta_parts.append(f"by {author}{author_marker}")
    lines.append(f"  {' | '.join(meta_parts)}")
    if comment_summary:
        lines.append(f"  💬 {comment_summary}")
    if story.get('source') == 'substack':
        lines.append(f"  🔗 {story.get('url', '')}")
    elif story_id:
        lines.append(f"  🔗 https://news.ycombinator.com/item?id={story_id}")
    else:
        lines.append(f"  🔗 {story.get('url', '')}")
    lines.append("  Notes: ")
    return lines


def generate_digest_text(result: Dict, config: Dict = None, weekend_sections=None) -> str:
    """Generate digest text from processed result.

    If weekend_sections is provided (a (top_matches, interesting_reads) tuple),
    renders the weekend layout instead of the standard topic-grouped layout.
    """
    stories = result['stories']
    notable_authors = result['notable_authors']
    engagement_opportunities = result.get('engagement_opportunities', [])

    if not stories:
        return "🦅 *HN Digest* - Quiet day on the frontier. Use the time to build.\n\n_No relevant stories today._"

    # ── Weekend layout ────────────────────────────────────────────────────────
    if weekend_sections is not None:
        top_matches, interesting_reads = weekend_sections
        wm = (config or {}).get("settings", {}).get("weekend_mode", {})
        title = wm.get("digest_title", "Weekend Reads")
        day_str = datetime.now().strftime("%a, %b %-d")

        lines = []
        lines.append(f"🌿 *{title}* — {day_str}")
        lines.append(f"_{len(top_matches)} top matches · {len(interesting_reads)} interesting reads_\n")

        lines.append("── Best Matches ──────────────────────")
        for story in top_matches:
            lines.extend(_format_story_lines(story, notable_authors))
        lines.append("")

        lines.append("── Interesting Reads ─────────────────")
        for story in interesting_reads:
            lines.extend(_format_story_lines(story, notable_authors))
        lines.append("")

        lines.append("_A quieter read for the weekend._")
        return "\n".join(lines)

    # ── Standard weekday layout ───────────────────────────────────────────────
    # Group by topic
    by_topic = {}
    for story in stories:
        topic = story['matched_topic']
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(story)

    # Build digest
    lines = []
    lines.append("🦅 *HN Digest* - Afternoon Energy Boost")
    lines.append(f"_{len(stories)} stories worth your attention_\n")
    
    # Add motivational context
    if notable_authors:
        lines.append("💡 *Signal:* Authors you're tracking posted today.\n")
    
    # Stories by topic
    for topic, topic_stories in by_topic.items():
        lines.append(f"*{topic}*")
        for story in topic_stories[:5]:  # Max 5 per topic
            lines.extend(_format_story_lines(story, notable_authors))
        lines.append("")  # Blank line between topics
    
    # Engagement opportunities section
    if ENGAGEMENT_ENABLED and engagement_opportunities:
        engagement_section = format_engagement_section(engagement_opportunities)
        if engagement_section:
            lines.append(engagement_section)
    
    # Notable authors section
    if notable_authors:
        lines.append("*Authors to Watch* ⭐")
        for author in notable_authors[:3]:
            topics = ", ".join(list(author['topics'].keys())[:3])
            lines.append(f"• {author['author_name']} ({author['story_count']} stories: {topics})")
        lines.append("")
    
    # Footer
    lines.append("")
    lines.append("_Keep building. The frontier moves forward._")
    lines.append("")
    lines.append("💬 *Feedback:* Reply with story numbers + action")
    lines.append("   Example: `1,3 👍  2 📌  4 skip`")

    return "\n".join(lines)

if __name__ == "__main__":
    # Load config
    config = load_config()
    
    # Read stories from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            stories = json.load(f)
    else:
        stories = json.load(sys.stdin)
    
    # Process stories
    result = process_stories(stories, config)

    # Check weekend mode
    wm = config.get("settings", {}).get("weekend_mode", {})
    weekend_sections = None
    if wm.get("enabled") and _is_weekend():
        scored_stories = result.get("all_scored_stories") or [
            (s, max(s.get("all_topic_scores", {}).values(), default=0.0))
            for s in result["stories"]
        ]
        weekend_sections = _apply_weekend_mode(scored_stories, config)

    # Generate digest
    digest = generate_digest_text(result, config=config, weekend_sections=weekend_sections)
    print(digest)
    
    # Save story metadata for feedback system
    metadata = {
        'stories': [
            {
                'id': s.get('id'),
                'title': s['title'],
                'url': s['url'],
                'score': s['score'],
                'by': s['by']
            }
            for s in result['stories'][:10]  # Max 10 for feedback
        ]
    }
    
    import json
    from pathlib import Path
    metadata_path = Path(__file__).parent / 'digest_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
