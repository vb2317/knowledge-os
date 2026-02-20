#!/usr/bin/env python3
"""
Match stories to topics using semantic similarity
"""
import json
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class TopicMatcher:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        
        # Load embedding model
        import sys
        print("Loading embedding model...", file=sys.stderr)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality
        
        # Pre-compute topic embeddings
        self.topic_embeddings = {}
        for topic in self.config['topics']:
            # Create topic representation from keywords
            topic_text = f"{topic['name']}. " + " ".join(topic['keywords'])
            self.topic_embeddings[topic['name']] = self.model.encode(topic_text)
    
    def match_stories(self, stories: List[Dict]) -> List[Dict]:
        """Match stories to topics and return filtered/enriched stories"""
        if not stories:
            return []
        
        # Embed story titles
        story_texts = [s['title'] for s in stories]
        story_embeddings = self.model.encode(story_texts)
        
        matched_stories = []
        threshold = self.config['settings']['similarity_threshold']
        
        for i, story in enumerate(stories):
            story_emb = story_embeddings[i].reshape(1, -1)
            
            # Calculate similarity to each topic
            topic_scores = {}
            for topic_name, topic_emb in self.topic_embeddings.items():
                similarity = cosine_similarity(story_emb, topic_emb.reshape(1, -1))[0][0]
                topic_scores[topic_name] = float(similarity)
            
            # Get best matching topic
            best_topic = max(topic_scores.items(), key=lambda x: x[1])
            
            if best_topic[1] >= threshold:
                story['matched_topic'] = best_topic[0]
                story['topic_score'] = best_topic[1]
                story['all_topic_scores'] = topic_scores
                matched_stories.append(story)
        
        # Sort by topic score (most relevant first)
        matched_stories.sort(key=lambda x: x['topic_score'], reverse=True)
        
        return matched_stories

if __name__ == "__main__":
    import sys
    
    # Read stories from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            stories = json.load(f)
    else:
        stories = json.load(sys.stdin)
    
    matcher = TopicMatcher()
    matched = matcher.match_stories(stories)
    
    print(json.dumps(matched, indent=2))
