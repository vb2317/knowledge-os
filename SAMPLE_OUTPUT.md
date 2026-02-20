# Sample Digest Output

**Last updated:** 2026-02-20  
**Test run:** Full pipeline with engagement detection

---

## Daily Digest (WhatsApp Format)

```
🦅 *HN Digest* - Afternoon Energy Boost
_4 stories worth your attention_

💡 *Signal:* Authors you're tracking posted today.

*AI/ML/LLMs*
• Measuring AI agent autonomy in practice
  ↑105 by jbredeche
  https://www.anthropic.com/research/measuring-agent-autonomy
  
• Don't Trust the Salt: AI Summarization, Multilingual Safety, and LLM Guardrails
  ↑211 by benbreen
  https://royapakzad.substack.com/p/multilingual-llm-evaluation-to-guardrails
  
• Consistency diffusion language models: Up to 14x faster, no quality loss
  ↑102 by zagwdt
  https://www.together.ai/blog/consistency-diffusion-language-models
  
• An AI Agent Published a Hit Piece on Me – The Operator Came Forward
  ↑366 by scottshambaugh ⭐
  https://theshamblog.com/an-ai-agent-wrote-a-hit-piece-on-me-part-4/


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
- **Format:** Topic heading, then stories
- **Fields:** Title, score (↑), author, URL
- **Marker:** ⭐ for notable/tracked authors
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
`stories_raw.json` (last fetch, 100 stories from HN)

---

## Notes

- Engagement section only appears when opportunities detected (5/day target)
- Notable authors only shown if they appear in current digest batch
- "Quiet day" message when no stories match topics
- WhatsApp formatting: markdown bold (*text*), no tables
