# Sample Digest Output

**Last updated:** 2026-03-01
**Test run:** Full pipeline with engagement detection, comment summaries, Substack source

---

## Daily Digest (WhatsApp Format)

```
🦅 *HN Digest* - Afternoon Energy Boost
_4 stories worth your attention_

💡 *Signal:* Authors you're tracking posted today.

*AI/ML/LLMs*
- [ ] Measuring AI agent autonomy in practice
  ↑105 | 87 comments | by jbredeche
  💬 Discussing: autonomy, evaluation, agents
  🔗 https://news.ycombinator.com/item?id=47075001
  Notes:

- [ ] 📰 How to Sound Like an Expert in Any AI Bubble Debate
  ↑0 | 0 comments | by Derek Thompson
  🔗 https://www.derekthompson.org/p/how-to-sound-like-an-expert-in-any
  Notes:

- [ ] Consistency diffusion language models: Up to 14x faster, no quality loss
  ↑102 | 43 comments | by zagwdt
  💬 Discussing: inference, speed, models
  🔗 https://news.ycombinator.com/item?id=47075002
  Notes:

- [ ] An AI Agent Published a Hit Piece on Me – The Operator Came Forward
  ↑366 | 302 comments | by scottshambaugh ⭐
  💬 Discussing: agents, operators, accountability
  🔗 https://news.ycombinator.com/item?id=47083145
  Notes:


🎯 *Engagement Opportunities*

💬 Show HN: Micasa – track your house from the terminal
   → Someone built something. 178 comments. Feedback or insights?
   https://news.ycombinator.com/item?id=47075124

💬 Show HN: A physically-based GPU ray tracer written in Julia
   → Someone built something. 75 comments. Feedback or insights?
   https://news.ycombinator.com/item?id=47072444

💬 Show HN: Ghostty-based terminal with vertical tabs and notifications
   → Someone built something. 60 comments. Feedback or insights?
   https://news.ycombinator.com/item?id=47079718

🔥 An AI Agent Published a Hit Piece on Me – The Operator Came Forward
   → Active debate (302 comments). Provide clarity or mental model?
   https://news.ycombinator.com/item?id=47083145

🔥 I tried building my startup entirely on European infrastructure
   → Active debate (59 comments). Provide clarity or mental model?
   https://news.ycombinator.com/item?id=47085483


*Authors to Watch* ⭐
• scottshambaugh (3 stories: AI/ML/LLMs, Data Science, Parenting/Education)

_Keep building. The frontier moves forward._
```

---

## Section Breakdown

### 📚 Matched Stories
- **Format:** Topic heading, then stories with inline `[ ]` checkboxes for read tracking
- **Fields:** Title, score (↑), comment count, author, optional comment summary (💬), URL
- **Marker:** ⭐ for notable/tracked authors; 📰 for Substack items
- **Limit:** Max 5 per topic

### 🎯 Engagement Opportunities (NEW)
- **Count:** 5 per digest
- **Types:** 
  - 💬 Ask/Show HN (explicit feedback requests)
  - 🎯 Early threads (<10 comments, <6h old)
  - 🔥 Hot debates (50+ comments, active)
- **Fields:** Title, action prompt, HN discussion link
- **Scoring:** Recency + comment activity + topic match

### 👤 Authors to Watch
- **Trigger:** Authors with 3+ stories across topics
- **Fields:** Name, story count, topics covered
- **Marker:** ⭐ appears on their stories in main section

---

## Output Files

**Digest text:**  
- `knos-digest/YYYY-MM-DD.md` (primary, markdown format)
- `archive/YYYY-MM-DD_digest.txt` (legacy, backward compatibility)

**Database:**  
`hn_digest_v2.db` (stories, topics, authors, engagement opportunities)

**Raw stories:**
`all_stories.json` (merged HN + Substack, last pipeline run)

---

## Notes

- Engagement section only appears when opportunities detected (5/day target)
- Notable authors only shown if they appear in current digest batch
- "Quiet day" message when no stories match topics
- WhatsApp formatting: markdown bold (*text*), no tables
