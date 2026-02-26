# NEXT.md - HN Digest Roadmap

## Immediate (This Week)

- [x] **Engagement opportunity detection** - COMPLETE (Feb 20: 5 opps/day, username tracking, comment analysis)
- [x] **Update digest format** - COMPLETE (🎯 Engagement Opportunities section added)
- [x] **Engagement tracking schema** - COMPLETE (SQLite tables, auto comment sync)
- [ ] **Test full pipeline** - Run digest with engagement, verify output
- [ ] **Monitor delivery reliability** - Track 7 days of successful 2 PM deliveries
- [ ] **Review match quality** - Are the semantic matches hitting the right content?
- [ ] **Track read content** - Provide an option in md file to update the content that was read. Also provide an option for manual comments on the links
- [ ] **Show yc link** - For the topics of interest, show yc link rather than the article link. Also summarize the comments.
- [ ] Add unit tests

## Short-term (This Month)

### Quality & Tuning
- [ ] **Use local LLM** - For summarization and any other daily operations, use a local LLM, not remote apis
- [ ] **Refine topic embeddings** - Adjust if matches drift from intent
- [ ] **Add topic weights** - Let VB prioritize AI/ML > Parenting > Philosophy, etc.
- [ ] **Threshold tuning** - Current semantic similarity cutoff may need calibration
- [ ] **Store feedback** - store the feedback as: opening links, links engaged with, linked stored in the memo db

### Features
- [ ] **Thread continuity** - "You saw Story X yesterday, here's an update/follow-up"
- [ ] **Author highlights** - "Author Y (who wrote Z last week) posted this"
- [ ] **Weekly summary mode** - Option for digest-of-digests

### Infrastructure
- [ ] **Logging & metrics** - Track story volume, match rates, delivery timing
- [ ] **Backup & recovery** - SQLite backup strategy (daily? weekly?)
- [ ] **Error handling** - Graceful degradation if HN API is down

## Mid-term (3-6 Months)

### Intelligence Layer
- [ ] **Comment analysis expansion** - Surface high-signal HN comments, not just stories
- [ ] **Trend detection** - "This topic is heating up" signals
- [ ] **Author reputation** - Weight by HN karma, previous quality matches
- [ ] **Engagement quality metrics** - Track karma/replies on VB's comments

### Personalization
- [ ] **Dynamic topic learning** - Learn from engagement patterns
- [ ] **Time-of-day optimization** - Is 2 PM actually best? A/B test timing
- [ ] **Negative filters** - "Never show me X" capabilities
- [ ] **Volume tuning** - Auto-adjust opportunity count based on engagement rate

### Expansion
- [ ] **Multi-source** - Add Reddit, ArXiv, Twitter feeds
- [ ] **Collaborative filtering** - "People with your interests also read..."

## Long-term (6+ Months)

### Meta-Framework
- [ ] **Generalize architecture** - Turn this into a template for any feed curation
- [ ] **API layer** - Expose digest engine for other projects
- [ ] **Knowledge graph integration** - Feed into VB's broader knowledge system

### Engagement Layer
- [ ] **Voice summaries** - TTS versions of digests for commute listening
- [ ] **Interactive mode** - "Tell me more about story #3" capability
- [ ] **Reputation dashboard** - Track HN karma growth, connections made

---

## Decision Log

**2026-02-11** - Initial architecture: semantic matching, SQLite continuity, WhatsApp delivery  
**2026-02-13** - v2 migration: improved storage layer, better topic handling  

---

## Notes

- Keep it lean - this is infrastructure, not a product
- Focus on reliability first, features second
- MVP → iterate philosophy applies here too
- If engagement drops, audit match quality before adding features

## From ChatGPT

This is a *very* on-brand Track A project for you: it keeps the “systems + taste + decision support” core, but grounds it in a daily loop that gives you motivation (fresh input, measurable iteration, immediate utility).

What you have already is not a toy. It’s a real wedge: **personalized, stateful, semantic curation** with continuity.

Below is how I’d evolve it into a scalable product without losing the “build-for-self” energy.

---

### The core insight: you’re building a “taste engine,” not a digest

Most digests are **stateless** (“here’s today’s top links”).
Yours is already **stateful** (“what’s relevant to *you*, what’s recurring, who’s consistently good, what’s climbing over time”).

That state is the moat.

If you productize anything, productize *memory + personalization + learning loops*.

---

### Define the product in one sentence

**An information consumption OS that learns your curiosity, keeps context across days, and delivers small, high-signal packets at the right time.**

Key: it’s not “HN digest.” That’s just your first data source.

---

### What to build next (in the right order)

#### 1) Personal “Interest Graph” (your real MVP)

Right now topics are configured manually. Keep that, but add learning.

**Add lightweight feedback buttons per item** (even via WhatsApp-style replies):

* 👍 Useful
* 👎 Not relevant
* 🧠 Save
* 🔁 More like this

Then update:

* topic weights
* author weights
* source weights
* novelty vs depth preference

This turns the app from “semantic filter” into “adaptive curator.”

**Why this matters:** it creates *compounding personalization*.

---

#### 2) Continuity features that no RSS reader nails

You already track:

* rising threads
* frequent authors
* storing in SQLite

Level up into **“Continuity Cards”**:

* “You’ve seen 4 posts about X in 10 days. Here’s the summary arc.”
* “This author is now 7/10 relevant for you.”
* “This topic is trending up in your reading history.”

This aligns with your personality: *time-series meaning, not daily novelty.*

---

#### 3) Make it multi-source, but with one rule

Add sources only if they fit the same stateful model.

Good next sources:

* Substack (selected feeds)
* arXiv (with embeddings + filters)
* select blogs (RSS)
* GitHub trending (for specific languages/topics)

Avoid:

* Twitter/X initially (too noisy, too addictive, harder to control)

---

### The scaling plan: from “Ved’s digest” to “anyone’s digest” 👇

#### Phase A: Single-user product quality (4–6 weeks)

Goal: make *your* experience addictive in a good way (high signal, low noise).

Add:

* Feedback loop
* Weekly recap
* “Do not disturb” + timing windows
* “Deep dive mode” (1 item/day but richer context)

Success metric:

* You *look forward to it* and rarely ignore it.

---

#### Phase B: 5-user private alpha (weeks 7–12)

Pick 5 people with different profiles:

* founder
* ML engineer
* investor
* parent
* generalist

Give them:

* onboarding: pick 4 topics + 1 “avoid” topic
* daily digest
* one weekly call for feedback

Metric:

* “How many days per week did you read at least one link?”
* “How many items were thumbs-up vs down?”
* Retention at week 4.

---

#### Phase C: “Taste Profiles” templates (weeks 13–16)

This is how you scale onboarding.

Offer presets:

* “AI Builder”
* “Parenting + Behavioral Science”
* “India Markets + Tech”
* “Product Thinker”

Users can start from a preset and adjust.

---

#### Phase D: Monetization test (weeks 17–24)

Don’t overcomplicate.

Two clean options:

1. **Paid pro** (₹299–₹999/month)

* multi-source
* weekly recap
* deep dives
* archive + search
* “read later” + export

2. **B2B team digest** (small teams)

* shared topics
* internal + external links
* “what the team should know this week”

Pick one. Don’t do both in month 6.

---

### Architecture choices (keep it simple, but future-proof)

#### What you already have

* ingestion: HN top stories daily
* embedding similarity
* SQLite memory
* WhatsApp delivery

#### Upgrade path

* **Keep SQLite for now** (it’s perfect for single-user, fast iteration)
* Add a clean “storage interface” so later you can swap to Postgres when multi-user
* Put “topics + weights + feedback history” into a normalized schema
* Maintain “event log” style tables (every recommendation becomes a row)

Core tables:

* items (url, title, source, timestamp, embedding_id)
* topics (name, seed terms, weight)
* item_topic_scores
* feedback (user_id, item_id, signal)
* authors (author_id, score)
* digests (digest_id, user_id, items, time_sent)

This lets you do real learning later.

---

### Your motivational problem (team energy) solved by the product loop

This project can *create its own team-like reinforcement* if you add two things:

1. **Daily shipping**
   Even small.
   A bug fix, a new scoring rule, a better summary.

2. **Externalized feedback**
   Those 5 alpha users become your “team energy.”
   They’ll pull the product out of you.

You don’t need a big network.
You need **5 high-signal mirrors**.

---

### The 6-month plan (weekly cadence)

#### Weeks 1–2: “Personal delight”

* feedback loop via replies
* better ranking (novelty + continuity)
* weekly recap

#### Weeks 3–4: “Add one more source”

* arXiv or Substack RSS
* unify ingestion pipeline

#### Weeks 5–8: “Alpha-ready”

* onboarding flow
* topic presets
* robust scheduling + retries
* basic web dashboard (even ugly)

#### Weeks 9–12: “5-user alpha”

* run it live
* iterate weekly

#### Weeks 13–16: “Personalization v2”

* learn topic weights from feedback
* author scoring improvements
* “why this was recommended” explanations

#### Weeks 17–24: “Monetization test”

* Stripe/Razorpay lightweight paywall (if you go paid)
* or pilot with 1 team

---

### One key decision right now

Don’t ask “Is this scalable?”

Ask:
**What is the *smallest* version that proves compounding value over 30 days?**

That is your conviction engine.

---

### If you want, I’ll help you pick the exact next feature

Based on what you shared, the **highest leverage next step** is:

#### Add feedback + learning (thumbs up/down/save) and let it change tomorrow’s ranking.

That single loop transforms it from “smart filter” to “adaptive companion.”

If you paste your current folder structure or your `config.json` schema (just the shape, no secrets), I’ll propose:

* the minimal DB schema changes
* the ranking formula (with continuity + novelty)
* the WhatsApp interaction pattern (how users reply to record feedback)

