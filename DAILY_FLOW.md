# Daily Flow: Digest + Engagement Summary

**Two separate messages at different times for different purposes**

---

## Message 1: HN Digest (2:00 PM)

**Purpose:** Discover today's HN opportunities  
**Frequency:** Daily  
**Format:**

```
🦅 *HN Digest* - Afternoon Energy Boost
_7 stories worth your attention_

*AI/ML/LLMs*
• Cord: Coordinating Trees of AI Agents
  ↑87 by gfortaine
  https://www.june.kim/cord

🎯 *Engagement Opportunities*

💬 Show HN: Native macOS HN client
   → Someone built something. 148 comments. Feedback?
   https://news.ycombinator.com/item?id=47088166

_Keep building. The frontier moves forward._
```

**What it shows:**
- 📚 Stories matched to your topics (AI/ML, Data Science, etc.)
- 🎯 5 engagement opportunities (Ask/Show HN, early, debates)
- ⭐ Notable authors you're tracking

**When skipped:**
- Never (always runs daily)
- Shows "quiet day" if no matches

---

## Message 2: Engagement Summary (5:00 PM)

**Purpose:** Reflect on today's HN engagement so far  
**Frequency:** Only when digest ran today  
**Format:**

```
📊 *Today's Engagement*

✅ *You engaged:* 4 comment(s) posted

💬 *Story 47088166* (was in opportunities)
  └ 15:13: This seems like a common problem...
    https://news.ycombinator.com/item?id=47099090
  └ 15:14: This feature is very useful :)
    https://news.ycombinator.com/item?id=47099101
  └ 15:43: This is fantastic. The app is simple...
    https://news.ycombinator.com/item?id=47099300
  └ 15:44: A link to my experiment: https://...
    https://news.ycombinator.com/item?id=47099309

*Opportunities:* 5 detected, 1 engaged (20%)

*Missed opportunities:*
💬 https://news.ycombinator.com/item?id=47094149
   Score: 1.00 · Someone built something. Feedback?
🔥 https://news.ycombinator.com/item?id=47094192
   Score: 0.85 · Active debate. Clarity?

*7-Day Trend*
Engagement rate: 7.7% (1/13)
💡 Tip: Low engagement - opportunities may be too broad

_Daily reflection · track engagement patterns_
```

**What it shows:**
- ✅ Comments you posted yesterday (time, snippet, link)
- 📊 Which stories were digest opportunities vs organic
- 📉 Missed opportunities with scores
- 📈 7-day engagement trend + tips

**When skipped:**
- No digest ran yesterday
- No engagement yesterday (0 comments)

---

## Message 2: HN Digest (2:00 PM)

**Purpose:** Discover today's HN opportunities  
**Frequency:** Daily  
**Format:**

```
🦅 *HN Digest* - Afternoon Energy Boost
_7 stories worth your attention_

*AI/ML/LLMs*
• Cord: Coordinating Trees of AI Agents
  ↑87 by gfortaine
  https://www.june.kim/cord

• Ggml.ai joins Hugging Face
  ↑733 by lairv
  https://github.com/ggml-org/llama.cpp/discussions/19759

*Parenting/Education*
• Child's Play: Tech's new generation
  ↑374 by ramimac
  https://harpers.org/archive/2026/03/...

🎯 *Engagement Opportunities*

💬 Show HN: Native macOS HN client
   → Someone built something. 148 comments. Feedback?
   https://news.ycombinator.com/item?id=47088166

🔥 Turn Dependabot off
   → Active debate (115 comments). Clarity?
   https://news.ycombinator.com/item?id=47094192

_Keep building. The frontier moves forward._
```

**What it shows:**
- 📚 Stories matched to your topics (AI/ML, Data Science, etc.)
- 🎯 5 engagement opportunities (Ask/Show HN, early, debates)
- ⭐ Notable authors you're tracking

**When skipped:**
- Never (always runs daily)
- Shows "quiet day" if no matches

---

## Why Separate?

### Different Purposes
- **Summary (AM):** Reflection, learning, calibration
- **Digest (PM):** Discovery, action, opportunities

### Different Frequencies
- **Summary:** Only when you engage (0-3x/week)
- **Digest:** Every day (7x/week)

### Different Timing
- **Summary:** Morning sets tone for day
- **Digest:** Afternoon catches hot stories

### Different Actions
- **Summary:** Review, reflect, adjust strategy
- **Digest:** Read, engage, contribute

---

## Sample Weekly Flow

### Monday
- **9 AM:** *(no summary - didn't engage Sunday)*
- **2 PM:** Digest arrives, 5 opportunities
- **Action:** Engage with 1 Ask HN

### Tuesday
- **9 AM:** Summary shows Monday's engagement (20% rate)
- **2 PM:** Digest arrives, 5 opportunities
- **Action:** Skip, nothing interesting

### Wednesday  
- **9 AM:** *(no summary - didn't engage Tuesday)*
- **2 PM:** Digest arrives, 5 opportunities
- **Action:** Engage with 2 debates

### Thursday
- **9 AM:** Summary shows Wednesday's engagement (40% rate)
- **2 PM:** Digest arrives, 5 opportunities
- **Action:** Engage with 1 Show HN

### Friday
- **9 AM:** Summary shows Thursday's engagement
- **2 PM:** Digest arrives, 5 opportunities
- **Action:** Engage with 1 early thread

### Saturday
- **9 AM:** Summary shows Friday's engagement
- **2 PM:** Digest arrives, 5 opportunities
- **Reflection:** 4/7 days engaged, 7/35 opportunities (20%)

---

## Benefits of Separation

### Morning Summary Benefits:
- ✅ Immediate feedback loop (see yesterday's impact)
- ✅ Calibrate engagement strategy before today's digest
- ✅ Track patterns (which opportunities you engage with)
- ✅ Builds reflection habit
- ✅ No clutter in main digest

### Afternoon Digest Benefits:
- ✅ Focused on discovery (not distracted by stats)
- ✅ Catches stories while hot (afternoon = engagement window)
- ✅ Clean, actionable format
- ✅ Independent of engagement tracking

---

## Message Comparison

| Aspect | Engagement Summary | HN Digest |
|--------|-------------------|-----------|
| **Time** | 9:00 AM | 2:00 PM |
| **Focus** | Past (yesterday) | Present (today) |
| **Purpose** | Reflection | Discovery |
| **Frequency** | Conditional | Daily |
| **Tone** | Analytical | Motivational |
| **Length** | Short (stats) | Medium (stories) |
| **Action** | Adjust strategy | Engage with HN |

---

## File Locations

**Summary:**
- Generator: `engagement_summary.py`
- Wrapper: `send_engagement_summary.sh`
- Cron: 9 AM daily (isolated session)

**Digest:**
- Generator: `process_digest.py`
- Wrapper: `daily_digest.sh` → `run_digest_v2.sh`
- Cron: 2 PM daily (isolated session)
- Archive: `knos-digest/YYYY-MM-DD.md`

**Shared:**
- Database: `hn_digest_v2.db`
- Engagement tracker: `engagement.py`

---

## Configuration

### Enable/Disable Summary

**Enable (recommended):**
```bash
# Add 9 AM cron job via OpenClaw
# See ENGAGEMENT_SUMMARY_PLAN.md for details
```

**Disable:**
```bash
# Remove cron job
# Digest continues unaffected
```

### Adjust Timing

**Morning summary:**
- 8 AM: Earlier reflection
- 9 AM: Standard (recommended)
- 10 AM: After morning routine

**Evening summary:**
- 9 PM: End-of-day recap
- Not recommended (less actionable)

---

## Implementation Status

### Completed ✅
- Summary generator (`engagement_summary.py`)
- Delivery wrapper (`send_engagement_summary.sh`)
- Testing with real data (Feb 21 engagement)
- Documentation (this file)

### To Do 🔲
- Add 9 AM cron job
- Test full delivery to WhatsApp
- Monitor for 7 days
- Iterate based on feedback

---

_Morning reflection + afternoon discovery = balanced engagement strategy_
