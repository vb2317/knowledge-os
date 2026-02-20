#!/usr/bin/env python3
"""
SQLite implementation of storage interface
"""
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
from storage_interface import StorageInterface

class SQLiteStorage(StorageInterface):
    def __init__(self, db_path: str = "hn_digest_v2.db"):
        self.db_path = db_path
        self.init_schema()
    
    def _get_conn(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_schema(self):
        """Initialize database schema"""
        conn = self._get_conn()
        c = conn.cursor()
        
        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT UNIQUE NOT NULL,
                settings TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Items table (core content)
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                author TEXT,
                score INTEGER,
                fetched_at TEXT NOT NULL,
                embedding_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url)
            )
        ''')
        
        # Topics table
        c.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                keywords TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, name)
            )
        ''')
        
        # Item-Topic scores (many-to-many)
        c.execute('''
            CREATE TABLE IF NOT EXISTS item_topic_scores (
                item_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                score REAL NOT NULL,
                computed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (item_id, topic_id),
                FOREIGN KEY (item_id) REFERENCES items(item_id),
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
            )
        ''')
        
        # Feedback events (event log)
        c.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        ''')
        
        # Authors table
        c.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT UNIQUE NOT NULL,
                story_count INTEGER DEFAULT 0,
                total_score REAL DEFAULT 0.0,
                topics TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Digests table (delivery log)
        c.execute('''
            CREATE TABLE IF NOT EXISTS digests (
                digest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_ids TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_items_url ON items(url)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_items_author ON items(author)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_digests_user ON digests(user_id)')
        
        conn.commit()
        conn.close()
    
    # Items
    def insert_item(self, url: str, title: str, source: str, author: str,
                   score: int, fetched_at: str, embedding_id: Optional[str] = None) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT OR IGNORE INTO items (url, title, source, author, score, fetched_at, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (url, title, source, author, score, fetched_at, embedding_id))
        
        if c.lastrowid:
            item_id = c.lastrowid
        else:
            # Already exists, get the ID
            c.execute('SELECT item_id FROM items WHERE url = ?', (url,))
            item_id = c.fetchone()['item_id']
        
        conn.commit()
        conn.close()
        return item_id
    
    def get_item(self, item_id: int) -> Optional[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_item_by_url(self, url: str) -> Optional[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM items WHERE url = ?', (url,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # Topics
    def insert_topic(self, user_id: int, name: str, keywords: List[str], weight: float = 1.0) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        
        keywords_json = json.dumps(keywords)
        c.execute('''
            INSERT OR REPLACE INTO topics (user_id, name, keywords, weight)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, keywords_json, weight))
        
        topic_id = c.lastrowid
        conn.commit()
        conn.close()
        return topic_id
    
    def get_topics(self, user_id: int) -> List[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM topics WHERE user_id = ?', (user_id,))
        rows = c.fetchall()
        conn.close()
        
        topics = []
        for row in rows:
            topic = dict(row)
            topic['keywords'] = json.loads(topic['keywords'])
            topics.append(topic)
        return topics
    
    def update_topic_weight(self, topic_id: int, weight: float):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('UPDATE topics SET weight = ?, updated_at = CURRENT_TIMESTAMP WHERE topic_id = ?',
                 (weight, topic_id))
        conn.commit()
        conn.close()
    
    # Item-Topic scores
    def insert_item_topic_score(self, item_id: int, topic_id: int, score: float):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO item_topic_scores (item_id, topic_id, score)
            VALUES (?, ?, ?)
        ''', (item_id, topic_id, score))
        conn.commit()
        conn.close()
    
    def get_item_topic_scores(self, item_id: int) -> List[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT its.*, t.name as topic_name
            FROM item_topic_scores its
            JOIN topics t ON its.topic_id = t.topic_id
            WHERE its.item_id = ?
        ''', (item_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # Feedback
    def insert_feedback(self, user_id: int, item_id: int, action: str,
                       metadata: Optional[Dict] = None):
        conn = self._get_conn()
        c = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        c.execute('''
            INSERT INTO feedback (user_id, item_id, action, metadata)
            VALUES (?, ?, ?, ?)
        ''', (user_id, item_id, action, metadata_json))
        
        conn.commit()
        conn.close()
    
    def get_feedback(self, user_id: int, item_id: Optional[int] = None) -> List[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        
        if item_id:
            c.execute('SELECT * FROM feedback WHERE user_id = ? AND item_id = ? ORDER BY created_at DESC',
                     (user_id, item_id))
        else:
            c.execute('SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 100',
                     (user_id,))
        
        rows = c.fetchall()
        conn.close()
        
        feedback = []
        for row in rows:
            fb = dict(row)
            if fb['metadata']:
                fb['metadata'] = json.loads(fb['metadata'])
            feedback.append(fb)
        return feedback
    
    # Authors
    def upsert_author(self, author_name: str, item_id: int, topic_scores: Dict[str, float]):
        conn = self._get_conn()
        c = conn.cursor()
        
        # Get existing author
        c.execute('SELECT * FROM authors WHERE author_name = ?', (author_name,))
        existing = c.fetchone()
        
        if existing:
            # Update
            existing_topics = json.loads(existing['topics']) if existing['topics'] else {}
            
            # Merge topic scores
            for topic, score in topic_scores.items():
                if topic in existing_topics:
                    existing_topics[topic] = max(existing_topics[topic], score)
                else:
                    existing_topics[topic] = score
            
            c.execute('''
                UPDATE authors
                SET story_count = story_count + 1,
                    total_score = total_score + ?,
                    topics = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE author_name = ?
            ''', (max(topic_scores.values()), json.dumps(existing_topics), author_name))
        else:
            # Insert
            c.execute('''
                INSERT INTO authors (author_name, story_count, total_score, topics)
                VALUES (?, 1, ?, ?)
            ''', (author_name, max(topic_scores.values()), json.dumps(topic_scores)))
        
        conn.commit()
        conn.close()
    
    def get_notable_authors(self, user_id: int, min_count: int = 3) -> List[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM authors
            WHERE story_count >= ?
            ORDER BY story_count DESC, total_score DESC
            LIMIT 20
        ''', (min_count,))
        
        rows = c.fetchall()
        conn.close()
        
        authors = []
        for row in rows:
            author = dict(row)
            author['topics'] = json.loads(author['topics']) if author['topics'] else {}
            authors.append(author)
        return authors
    
    # Digests
    def insert_digest(self, user_id: int, item_ids: List[int], sent_at: str) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO digests (user_id, item_ids, sent_at)
            VALUES (?, ?, ?)
        ''', (user_id, json.dumps(item_ids), sent_at))
        
        digest_id = c.lastrowid
        conn.commit()
        conn.close()
        return digest_id
    
    def get_digest_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM digests
            WHERE user_id = ?
            ORDER BY sent_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = c.fetchall()
        conn.close()
        
        digests = []
        for row in rows:
            digest = dict(row)
            digest['item_ids'] = json.loads(digest['item_ids'])
            if digest['metadata']:
                digest['metadata'] = json.loads(digest['metadata'])
            digests.append(digest)
        return digests
    
    # Users
    def get_or_create_user(self, identifier: str, settings: Optional[Dict] = None) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('SELECT user_id FROM users WHERE identifier = ?', (identifier,))
        row = c.fetchone()
        
        if row:
            user_id = row['user_id']
        else:
            settings_json = json.dumps(settings) if settings else None
            c.execute('''
                INSERT INTO users (identifier, settings)
                VALUES (?, ?)
            ''', (identifier, settings_json))
            user_id = c.lastrowid
            conn.commit()
        
        conn.close()
        return user_id
