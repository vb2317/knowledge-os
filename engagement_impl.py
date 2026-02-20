#!/usr/bin/env python3
"""
Engagement Opportunity Detection for HN Digest
Add to existing process_digest.py or use as standalone module
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any


class EngagementDetector:
    """Detect and score engagement opportunities from HN stories"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create engagement tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS engagement_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER,
                detected_date TEXT,
                opportunity_type TEXT,
                score REAL,
                action_prompt TEXT,
                engaged BOOLEAN DEFAULT 0,
                engagement_date TEXT,
                comment_url TEXT,
                karma_gained INTEGER,
                FOREIGN KEY (story_id) REFERENCES stories(id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS engagement_stats (
                date TEXT PRIMARY KEY,
                opportunities_detected INTEGER,
                opportunities_engaged INTEGER,
                total_karma_gained INTEGER,
                replies_received INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def detect_opportunities(self, stories: List[Dict], max_results: int = 3) -> List[Dict]:
        """
        Find top engagement opportunities from matched stories
        
        Args:
            stories: List of HN story dicts with title, url, descendants, score, etc.
            max_results: Maximum opportunities to return
            
        Returns:
            List of opportunity dicts with type, story, score, action_prompt
        """
        opportunities = []
        
        for story in stories:
            # Type 1: Ask HN / Show HN
            if story['title'].startswith(('Ask HN:', 'Show HN:')):
                opportunities.append({
                    'type': 'ask_show',
                    'story': story,
                    'score': self._score_ask_show(story),
                    'action_prompt': self._generate_ask_show_prompt(story)
                })
            
            # Type 2: Early engagement (low comment count)
            elif story.get('descendants', 0) < 10:
                opportunities.append({
                    'type': 'early',
                    'story': story,
                    'score': self._score_early(story),
                    'action_prompt': self._generate_early_prompt(story)
                })
            
            # Type 3: Hot debate (50+ comments, recent)
            elif story.get('descendants', 0) > 50:
                opportunities.append({
                    'type': 'debate',
                    'story': story,
                    'score': self._score_debate(story),
                    'action_prompt': self._generate_debate_prompt(story)
                })
        
        # Sort by score and return top N
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities[:max_results]
    
    def _score_ask_show(self, story: Dict) -> float:
        """Score Ask HN / Show HN opportunities"""
        base_score = 0.7  # High base - explicit request for feedback
        
        # Boost for low comment count (early engagement)
        comment_boost = 0.2 if story.get('descendants', 0) < 5 else 0.1
        
        # Boost for recent (assume time < 6h)
        time_boost = 0.1  # TODO: calculate from story['time']
        
        return min(1.0, base_score + comment_boost + time_boost)
    
    def _score_early(self, story: Dict) -> float:
        """Score early engagement opportunities"""
        base_score = 0.5
        
        # Higher score for 0-3 comments (very early)
        comment_count = story.get('descendants', 0)
        if comment_count == 0:
            comment_boost = 0.3
        elif comment_count <= 3:
            comment_boost = 0.2
        else:
            comment_boost = 0.1
        
        # Boost for high score (popular story)
        score_boost = 0.1 if story.get('score', 0) > 50 else 0.05
        
        return min(1.0, base_score + comment_boost + score_boost)
    
    def _score_debate(self, story: Dict) -> float:
        """Score debate/discussion opportunities"""
        base_score = 0.4  # Lower base - harder to stand out
        
        # Boost for very active discussions
        comment_count = story.get('descendants', 0)
        if comment_count > 100:
            activity_boost = 0.3
        elif comment_count > 75:
            activity_boost = 0.2
        else:
            activity_boost = 0.1
        
        return min(1.0, base_score + activity_boost)
    
    def _generate_ask_show_prompt(self, story: Dict) -> str:
        """Generate action prompt for Ask/Show HN"""
        comment_count = story.get('descendants', 0)
        title = story['title']
        
        if title.startswith('Ask HN:'):
            return f"Direct question. {comment_count} comments so far. Share your experience?"
        else:  # Show HN
            return f"Someone built something. {comment_count} comments. Provide feedback or related insights?"
    
    def _generate_early_prompt(self, story: Dict) -> str:
        """Generate action prompt for early engagement"""
        comment_count = story.get('descendants', 0)
        return f"Early conversation ({comment_count} comments). High visibility opportunity. Add value?"
    
    def _generate_debate_prompt(self, story: Dict) -> str:
        """Generate action prompt for debates"""
        comment_count = story.get('descendants', 0)
        return f"Active debate ({comment_count} comments). Provide framework or clarity?"
    
    def save_opportunities(self, opportunities: List[Dict], date: str):
        """Save detected opportunities to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        for opp in opportunities:
            c.execute('''
                INSERT INTO engagement_opportunities 
                (story_id, detected_date, opportunity_type, score, action_prompt)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                opp['story']['id'],
                date,
                opp['type'],
                opp['score'],
                opp['action_prompt']
            ))
        
        # Update stats
        c.execute('''
            INSERT OR REPLACE INTO engagement_stats 
            (date, opportunities_detected)
            VALUES (?, ?)
        ''', (date, len(opportunities)))
        
        conn.commit()
        conn.close()
    
    def mark_engaged(self, story_id: int, comment_url: str, karma_gained: int = 0):
        """Mark an opportunity as engaged"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            UPDATE engagement_opportunities 
            SET engaged = 1, engagement_date = ?, comment_url = ?, karma_gained = ?
            WHERE story_id = ?
        ''', (datetime.now().isoformat(), comment_url, karma_gained, story_id))
        
        conn.commit()
        conn.close()


def format_engagement_section(opportunities: List[Dict]) -> str:
    """
    Format opportunities for digest output
    
    Args:
        opportunities: List of opportunity dicts
        
    Returns:
        Formatted text for WhatsApp digest
    """
    if not opportunities:
        return ""
    
    output = "\n🎯 *Engagement Opportunities*\n\n"
    
    for i, opp in enumerate(opportunities, 1):
        story = opp['story']
        title = story['title']
        url = f"https://news.ycombinator.com/item?id={story['id']}"
        
        # Emoji by type
        emoji = {
            'ask_show': '💬',
            'early': '🎯',
            'debate': '🔥'
        }.get(opp['type'], '•')
        
        output += f"{emoji} *{title}*\n"
        output += f"   → {opp['action_prompt']}\n"
        output += f"   {url}\n\n"
    
    return output


# Example integration with existing digest flow
if __name__ == "__main__":
    # Test with dummy data
    detector = EngagementDetector("/tmp/test_digest.db")
    
    test_stories = [
        {
            'id': 12345,
            'title': 'Ask HN: Best practices for ML in production?',
            'descendants': 3,
            'score': 45,
            'url': 'https://news.ycombinator.com/item?id=12345'
        },
        {
            'id': 67890,
            'title': 'Show HN: I built a knowledge graph tool',
            'descendants': 2,
            'score': 78,
            'url': 'https://news.ycombinator.com/item?id=67890'
        }
    ]
    
    opportunities = detector.detect_opportunities(test_stories)
    detector.save_opportunities(opportunities, datetime.now().date().isoformat())
    
    print(format_engagement_section(opportunities))
