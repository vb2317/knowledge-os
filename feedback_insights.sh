#!/bin/bash
# Quick feedback analytics from hn_feedback.db

DB="$(dirname "$0")/hn_feedback.db"

if [ ! -f "$DB" ]; then
    echo "❌ No feedback database found. Run extract_feedback_simple.py first."
    exit 1
fi

echo "📊 HN Digest Feedback Analytics"
echo "================================"
echo

echo "🔢 Overall Stats"
echo "----------------"
sqlite3 -column -header "$DB" << 'SQL'
SELECT 
    COUNT(*) as Total,
    SUM(CASE WHEN action='like' THEN 1 ELSE 0 END) as Liked,
    SUM(CASE WHEN action='save' THEN 1 ELSE 0 END) as Saved,
    SUM(CASE WHEN action='skip' THEN 1 ELSE 0 END) as Skipped
FROM feedback;
SQL
echo

echo "📌 Saved Stories (with notes)"
echo "-----------------------------"
sqlite3 "$DB" << 'SQL'
SELECT 
    '• ' || story_title || CHAR(10) || 
    '  ' || story_url || CHAR(10) ||
    '  📝 ' || substr(notes, 1, 100) || '...'
FROM feedback 
WHERE action='save' AND notes != ''
ORDER BY timestamp DESC;
SQL
echo

echo "👍 Liked Stories"
echo "----------------"
sqlite3 "$DB" << 'SQL'
SELECT '• ' || story_title || ' (by ' || story_author || ')'
FROM feedback 
WHERE action='like'
ORDER BY timestamp DESC
LIMIT 10;
SQL
echo

echo "📈 Engagement by Date"
echo "---------------------"
sqlite3 -column -header "$DB" << 'SQL'
SELECT 
    digest_date as Date,
    COUNT(*) as Total,
    SUM(CASE WHEN action='like' THEN 1 ELSE 0 END) as Liked,
    SUM(CASE WHEN action='save' THEN 1 ELSE 0 END) as Saved
FROM feedback
GROUP BY digest_date
ORDER BY digest_date DESC
LIMIT 10;
SQL
echo

echo "✨ Top Authors (from liked/saved stories)"
echo "------------------------------------------"
sqlite3 -column -header "$DB" << 'SQL'
SELECT 
    story_author as Author,
    COUNT(*) as Count
FROM feedback 
WHERE action IN ('like', 'save') AND story_author IS NOT NULL
GROUP BY story_author
ORDER BY Count DESC
LIMIT 10;
SQL
