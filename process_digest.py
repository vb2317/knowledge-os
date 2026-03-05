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
    """
    Generate a 1-line summary of HN comments for digest display.
    Simple extractive approach: pull key themes from top comments.
    """
    if not comments:
        if descendants:
            return f"{descendants} comments"
        return None

    stop_words = {
        'this', 'that', 'have', 'with', 'they', 'from', 'were', 'been',
        'would', 'could', 'should', 'about', 'which', 'their', 'there',
        'what', 'when', 'will', 'more', 'some', 'than', 'them', 'like',
        'just', 'also', 'into', 'very', 'does', 'your', 'much', 'most',
        'each', 'only', 'even', 'want', 'really', 'think', 'know', 'people',
        'thing', 'things', 'using', 'being', 'well', 'still', 'though',
    }

    # Extract first sentences from top 5 comments
    sentences = []
    for comment in comments[:5]:
        text = comment.get('text', '')
        if not text:
            continue
        sent = _extract_first_sentence(text)
        if sent:
            sentences.append(sent)

    if not sentences:
        if descendants:
            return f"{descendants} comments"
        return None

    # Extract key themes
    keywords = _extract_keywords(sentences, stop_words)
    if keywords:
        themes = ", ".join(keywords[:3])
        return f"Discussing: {themes}"

    # Fallback
    return f"{descendants or len(comments)} comments"


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
    matcher = TopicMatcher(config_path="config.json")
    matched_stories = matcher.match_stories(stories)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Topic matching completed in {time.time() - matcher_start:.1f}s ({len(matched_stories)} matched)", file=sys.stderr)
    
    # Process each story
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Storing {len(matched_stories)} stories in database...", file=sys.stderr)
    db_start = time.time()
    item_ids = []
    new_stories = []
    notable_authors = []
    continuing_threads = []

    for story in matched_stories:
        # Insert item — is_new=False means already delivered in a prior digest
        item_id, is_new = storage.insert_item(
            url=story['url'],
            title=story['title'],
            source=story.get('source', 'hackernews'),
            author=story['by'],
            score=story['score'],
            fetched_at=story['fetched_at'],
            published_at=story.get('published_at', ''),
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
            author_name=story['by'],
            item_id=item_id,
            topic_scores=story['all_topic_scores']
        )

        # Only surface new stories in the digest
        if is_new:
            item_ids.append(item_id)
            new_stories.append(story)

    matched_stories = new_stories
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Database storage completed in {time.time() - db_start:.1f}s ({len(matched_stories)} new)", file=sys.stderr)
    
    # Get notable authors
    authors_start = time.time()
    notable_authors = storage.get_notable_authors(
        user_id=user_id,
        min_count=config['settings']['notable_author_threshold']
    )
    
    # Filter notable authors that appear in current batch
    current_authors = {s['by'] for s in matched_stories}
    batch_notable = [a for a in notable_authors if a['author_name'] in current_authors]
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

    # Fetch comment summaries for matched stories
    if ENGAGEMENT_ENABLED and matched_stories:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching comment summaries...", file=sys.stderr)
        comments_start = time.time()
        try:
            db_config = config['storage']['sqlite']
            comment_detector = EngagementDetector(db_config['db_path'])
            for story in matched_stories:
                story_id = story.get('id')
                if not story_id:
                    continue
                try:
                    comments = comment_detector.fetch_story_comments(story_id, max_depth=1)
                    story['comment_summary'] = summarize_comments(comments, story.get('descendants', 0))
                except Exception:
                    story['comment_summary'] = None
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Comment summaries fetched in {time.time() - comments_start:.1f}s", file=sys.stderr)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Comment summarization failed: {e}", file=sys.stderr)

    # Detect engagement opportunities
    engagement_opportunities = []
    if ENGAGEMENT_ENABLED and matched_stories:
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
        'stories': matched_stories,
        'notable_authors': batch_notable,
        'digest_id': digest_id,
        'item_ids': item_ids,
        'engagement_opportunities': engagement_opportunities
    }

def generate_digest_text(result: Dict) -> str:
    """Generate digest text from processed result"""
    stories = result['stories']
    notable_authors = result['notable_authors']
    engagement_opportunities = result.get('engagement_opportunities', [])
    
    if not stories:
        return "🦅 *HN Digest* - Quiet day on the frontier. Use the time to build.\n\n_No relevant stories today._"
    
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
            title = story['title']
            score = story['score']
            author = story['by']
            story_id = story.get('id')
            descendants = story.get('descendants', 0)
            comment_summary = story.get('comment_summary')

            # Check if author is notable
            author_marker = ""
            if notable_authors:
                for notable in notable_authors:
                    if notable['author_name'] == author:
                        author_marker = " ⭐"
                        break

            # Comment count display
            comment_str = f"{descendants} comments" if descendants else "0 comments"

            source_icon = "📰 " if story.get('source') == 'substack' else ""
            lines.append(f"- [ ] {source_icon}{title}")
            lines.append(f"  ↑{score} | {comment_str} | by {author}{author_marker}")
            if comment_summary:
                lines.append(f"  💬 {comment_summary}")
            # Use HN discussion link for HN stories, article URL for other sources
            if story.get('source') == 'substack':
                lines.append(f"  🔗 {story.get('url', '')}")
            elif story_id:
                lines.append(f"  🔗 https://news.ycombinator.com/item?id={story_id}")
            else:
                lines.append(f"  🔗 {story.get('url', '')}")
            lines.append(f"  Notes: ")
        
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
    lines.append("_Keep building. The frontier moves forward._")

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
    
    # Generate digest
    digest = generate_digest_text(result)
    print(digest)
