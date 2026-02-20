#!/usr/bin/env python3
"""
Main digest processing pipeline using new storage architecture
"""
import json
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

def process_stories(stories: List[Dict], config: Dict) -> Dict:
    """Process stories through the new storage pipeline"""
    
    # Initialize storage
    storage_config = config['storage']
    storage = get_storage(
        backend=storage_config['backend'],
        **storage_config.get(storage_config['backend'], {})
    )
    
    # Get or create user
    user_id = storage.get_or_create_user(
        identifier=config['user']['identifier']
    )
    
    # Initialize topics if needed
    existing_topics = storage.get_topics(user_id)
    if not existing_topics:
        for topic in config['topics']:
            storage.insert_topic(
                user_id=user_id,
                name=topic['name'],
                keywords=topic['keywords'],
                weight=topic.get('weight', 1.0)
            )
        existing_topics = storage.get_topics(user_id)
    
    # Match topics using existing matcher
    matcher = TopicMatcher(config_path="config.json")
    matched_stories = matcher.match_stories(stories)
    
    # Process each story
    item_ids = []
    notable_authors = []
    continuing_threads = []
    
    for story in matched_stories:
        # Insert item
        item_id = storage.insert_item(
            url=story['url'],
            title=story['title'],
            source='hackernews',
            author=story['by'],
            score=story['score'],
            fetched_at=story['fetched_at']
        )
        
        item_ids.append(item_id)
        
        # Store topic scores
        for topic in existing_topics:
            if topic['name'] in story['all_topic_scores']:
                score = story['all_topic_scores'][topic['name']]
                storage.insert_item_topic_score(
                    item_id=item_id,
                    topic_id=topic['topic_id'],
                    score=score
                )
        
        # Update author stats
        storage.upsert_author(
            author_name=story['by'],
            item_id=item_id,
            topic_scores=story['all_topic_scores']
        )
    
    # Get notable authors
    notable_authors = storage.get_notable_authors(
        user_id=user_id,
        min_count=config['settings']['notable_author_threshold']
    )
    
    # Filter notable authors that appear in current batch
    current_authors = {s['by'] for s in matched_stories}
    batch_notable = [a for a in notable_authors if a['author_name'] in current_authors]
    
    # Record digest
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

    # Detect engagement opportunities
    engagement_opportunities = []
    if ENGAGEMENT_ENABLED and matched_stories:
        try:
            # Get raw stories with HN data for engagement detection
            db_config = config['storage']['sqlite']
            detector = EngagementDetector(db_config['db_path'])
            engagement_opportunities = detector.detect_opportunities(stories, max_results=5)
            detector.save_opportunities(engagement_opportunities, datetime.now().date().isoformat())
            
            # Sync user comments in background
            detector.sync_user_comments()
        except Exception as e:
            print(f"Warning: Engagement detection failed: {e}", file=sys.stderr)
    
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
            url = story['url']
            
            # Check if author is notable
            author_marker = ""
            if notable_authors:
                for notable in notable_authors:
                    if notable['author_name'] == author:
                        author_marker = " ⭐"
                        break
            
            lines.append(f"• {title}")
            lines.append(f"  ↑{score} by {author}{author_marker}")
            lines.append(f"  {url}")
        
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
