#!/usr/bin/env python3
"""
knowledge-os local dashboard
Run with: venv/bin/python -m streamlit run dashboard.py
"""
import json
import sqlite3
import sys
import urllib.request
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

DB_PATH = "hn_digest_v2.db"
CONFIG_PATH = "config.json"

st.set_page_config(layout="wide", page_title="knowledge-os", page_icon="🦅")


# ── Helpers ─────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


@st.cache_resource(show_spinner="Loading embedding model…")
def get_topic_matcher():
    from match_topics import TopicMatcher
    return TopicMatcher(config_path=CONFIG_PATH)


def query(sql, params=()):
    conn = get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def scalar(sql, params=()):
    conn = get_conn()
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


# ── App shell ────────────────────────────────────────────────────────────────

st.title("🦅 knowledge-os")
tabs = st.tabs(["Overview", "Config", "Stories", "Authors", "Simulator"])


# ── Tab 1: Overview ──────────────────────────────────────────────────────────

with tabs[0]:
    st.header("Overview")

    # Core counts
    total_items = scalar("SELECT COUNT(*) FROM items") or 0
    hn_items = scalar("SELECT COUNT(*) FROM items WHERE source = 'hackernews'") or 0
    sub_items = scalar("SELECT COUNT(*) FROM items WHERE source = 'substack'") or 0
    total_digests = scalar("SELECT COUNT(*) FROM digests") or 0
    last_digest = scalar("SELECT MAX(sent_at) FROM digests")
    notable_authors = scalar("SELECT COUNT(*) FROM authors WHERE story_count >= 3") or 0

    # Engagement stats (table may not exist on fresh DB)
    try:
        eng_detected = scalar("SELECT COALESCE(SUM(1),0) FROM engagement_opportunities") or 0
        eng_engaged = scalar("SELECT COALESCE(SUM(CASE WHEN engaged=1 THEN 1 ELSE 0 END),0) FROM engagement_opportunities") or 0
    except Exception:
        eng_detected = eng_engaged = 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total items", total_items)
    col2.metric("HN items", hn_items)
    col3.metric("Substack items", sub_items)
    col4.metric("Digests sent", total_digests)
    col5.metric("Notable authors", notable_authors)
    col6.metric("Eng. opps (engaged)", f"{eng_detected} ({eng_engaged})")

    if last_digest:
        st.caption(f"Last digest: {last_digest[:19]}")

    st.divider()

    # Items by topic
    topic_counts = query("""
        SELECT t.name AS topic, COUNT(its.item_id) AS count
        FROM item_topic_scores its
        JOIN topics t ON its.topic_id = t.topic_id
        WHERE its.score = (
            SELECT MAX(its2.score)
            FROM item_topic_scores its2
            WHERE its2.item_id = its.item_id
        )
        GROUP BY t.name
        ORDER BY count DESC
    """)
    if topic_counts:
        st.subheader("Items by top topic")
        df_topics = pd.DataFrame(topic_counts).set_index("topic")
        st.bar_chart(df_topics["count"])

    st.divider()

    # Recent digest history
    digests = query("""
        SELECT digest_id, sent_at,
               LENGTH(item_ids) - LENGTH(REPLACE(item_ids, ',', '')) + 1 AS item_count
        FROM digests ORDER BY sent_at DESC LIMIT 10
    """)
    if digests:
        st.subheader("Recent digests")
        st.dataframe(pd.DataFrame(digests), use_container_width=True, hide_index=True)


# ── Tab 2: Config ────────────────────────────────────────────────────────────

with tabs[1]:
    st.header("Config")
    cfg = load_config()

    # ── Topics ──
    with st.expander("Topics", expanded=True):
        with st.form("topics_form"):
            updated_topics = []
            for i, topic in enumerate(cfg["topics"]):
                st.markdown(f"**{topic['name']}**")
                c1, c2 = st.columns([3, 1])
                kw_raw = c1.text_input(
                    "Keywords (comma-separated)",
                    value=", ".join(topic["keywords"]),
                    key=f"kw_{i}",
                )
                weight = c2.slider(
                    "Weight",
                    min_value=0.1,
                    max_value=2.0,
                    value=float(topic.get("weight", 1.0)),
                    step=0.1,
                    key=f"w_{i}",
                )
                updated_topics.append({
                    "name": topic["name"],
                    "keywords": [k.strip() for k in kw_raw.split(",") if k.strip()],
                    "weight": weight,
                })
                st.markdown("---")

            new_topic_name = st.text_input("Add new topic name")
            new_topic_kw = st.text_input("Keywords for new topic (comma-separated)")

            if st.form_submit_button("Save topics"):
                if new_topic_name.strip():
                    updated_topics.append({
                        "name": new_topic_name.strip(),
                        "keywords": [k.strip() for k in new_topic_kw.split(",") if k.strip()],
                        "weight": 1.0,
                    })
                cfg["topics"] = updated_topics
                save_config(cfg)
                st.success("Topics saved.")
                st.cache_resource.clear()  # Force matcher reload

        # Remove topic
        topic_names = [t["name"] for t in cfg["topics"]]
        remove_name = st.selectbox("Remove topic", ["— select —"] + topic_names)
        if st.button("Remove selected topic") and remove_name != "— select —":
            cfg["topics"] = [t for t in cfg["topics"] if t["name"] != remove_name]
            save_config(cfg)
            st.success(f"Removed {remove_name}.")
            st.rerun()

    # ── Sources ──
    with st.expander("Sources"):
        with st.form("sources_form"):
            hn_enabled = st.checkbox(
                "Hacker News enabled",
                value=cfg["sources"]["hackernews"].get("enabled", True),
            )
            sub_enabled = st.checkbox(
                "Substack enabled",
                value=cfg["sources"]["substack"].get("enabled", True),
            )
            feeds_raw = st.text_area(
                "Substack feeds (one URL per line)",
                value="\n".join(cfg["sources"]["substack"].get("feeds", [])),
                height=120,
            )
            sub_max = st.number_input(
                "Max Substack items per feed",
                min_value=1,
                max_value=50,
                value=int(cfg["sources"]["substack"].get("max_items", 10)),
            )
            if st.form_submit_button("Save sources"):
                cfg["sources"]["hackernews"]["enabled"] = hn_enabled
                cfg["sources"]["substack"]["enabled"] = sub_enabled
                cfg["sources"]["substack"]["feeds"] = [
                    u.strip() for u in feeds_raw.splitlines() if u.strip()
                ]
                cfg["sources"]["substack"]["max_items"] = int(sub_max)
                save_config(cfg)
                st.success("Sources saved.")

    # ── Settings ──
    with st.expander("Settings"):
        with st.form("settings_form"):
            s = cfg["settings"]
            max_stories = st.slider("max_stories", 5, 100, int(s.get("max_stories", 30)))
            min_score = st.slider("min_score (HN upvotes)", 0, 500, int(s.get("min_score", 50)))
            sim_thresh = st.slider(
                "similarity_threshold",
                0.0, 1.0, float(s.get("similarity_threshold", 0.3)), step=0.01,
            )
            notable_thresh = st.number_input(
                "notable_author_threshold",
                min_value=1,
                max_value=20,
                value=int(s.get("notable_author_threshold", 3)),
            )
            digest_time = st.text_input("digest_time (HH:MM)", value=s.get("digest_time", "14:00"))
            if st.form_submit_button("Save settings"):
                cfg["settings"]["max_stories"] = max_stories
                cfg["settings"]["min_score"] = min_score
                cfg["settings"]["similarity_threshold"] = sim_thresh
                cfg["settings"]["notable_author_threshold"] = int(notable_thresh)
                cfg["settings"]["digest_time"] = digest_time
                save_config(cfg)
                st.success("Settings saved.")

    st.caption(f"Config file: `{CONFIG_PATH}`")


# ── Tab 3: Stories ───────────────────────────────────────────────────────────

with tabs[2]:
    st.header("Stories")

    # Sidebar-style filters in a top row
    f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1, 2])
    source_filter = f1.selectbox("Source", ["All", "hackernews", "substack"])
    min_score_filter = f2.number_input("Min score", min_value=0, value=0, step=10)
    days_back = f3.number_input("Days back", min_value=1, max_value=365, value=30)
    topic_options = ["All"] + [t["name"] for t in load_config()["topics"]]
    topic_filter = f4.selectbox("Topic", topic_options)
    author_filter = f5.text_input("Author contains")

    cutoff = (datetime.now() - timedelta(days=int(days_back))).isoformat()

    # Build query
    base_sql = """
        SELECT i.item_id, i.title, i.source, i.author, i.score,
               i.fetched_at, i.url
        FROM items i
        WHERE i.fetched_at >= ?
          AND i.score >= ?
    """
    params = [cutoff, min_score_filter]

    if source_filter != "All":
        base_sql += " AND i.source = ?"
        params.append(source_filter)

    if author_filter.strip():
        base_sql += " AND i.author LIKE ?"
        params.append(f"%{author_filter.strip()}%")

    if topic_filter != "All":
        base_sql += """
            AND i.item_id IN (
                SELECT its.item_id FROM item_topic_scores its
                JOIN topics t ON its.topic_id = t.topic_id
                WHERE t.name = ?
                AND its.score = (
                    SELECT MAX(its2.score) FROM item_topic_scores its2
                    WHERE its2.item_id = its.item_id
                )
            )
        """
        params.append(topic_filter)

    base_sql += " ORDER BY i.fetched_at DESC LIMIT 500"

    rows = query(base_sql, params)
    st.caption(f"{len(rows)} items")

    if rows:
        df = pd.DataFrame(rows)
        df["fetched_at"] = df["fetched_at"].str[:19]

        # Paginate
        page_size = 25
        total_pages = max(1, (len(df) - 1) // page_size + 1)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1
        page_df = df.iloc[page * page_size:(page + 1) * page_size]

        selected = st.dataframe(
            page_df[["item_id", "title", "source", "author", "score", "fetched_at"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        # Expand selected row
        sel_rows = selected.selection.rows if hasattr(selected, "selection") else []
        if sel_rows:
            sel_item_id = page_df.iloc[sel_rows[0]]["item_id"]
            st.markdown(f"**URL:** {page_df.iloc[sel_rows[0]]['url']}")
            topic_scores = query("""
                SELECT t.name, its.score
                FROM item_topic_scores its
                JOIN topics t ON its.topic_id = t.topic_id
                WHERE its.item_id = ?
                ORDER BY its.score DESC
            """, [sel_item_id])
            if topic_scores:
                st.markdown("**Topic scores:**")
                ts_df = pd.DataFrame(topic_scores)
                st.bar_chart(ts_df.set_index("name")["score"])


# ── Tab 4: Authors ───────────────────────────────────────────────────────────

with tabs[3]:
    st.header("Authors")

    a1, a2 = st.columns(2)
    min_stories = a1.number_input("Min story count", min_value=1, value=1)
    sort_by = a2.selectbox("Sort by", ["story_count", "total_score", "last_seen"])

    authors = query(f"""
        SELECT author_name, story_count, total_score, topics, last_seen, first_seen
        FROM authors
        WHERE story_count >= ?
        ORDER BY {sort_by} DESC
        LIMIT 200
    """, [min_stories])

    if authors:
        # Parse topics JSON and render as tag string
        rows_display = []
        for a in authors:
            topic_dict = json.loads(a["topics"]) if a["topics"] else {}
            top_topics = sorted(topic_dict.items(), key=lambda x: x[1], reverse=True)[:3]
            tags = " · ".join(f"{k} ({v:.2f})" for k, v in top_topics)
            rows_display.append({
                "author": a["author_name"],
                "stories": a["story_count"],
                "total_score": round(float(a["total_score"]), 3),
                "top topics": tags,
                "last_seen": (a["last_seen"] or "")[:10],
            })
        st.dataframe(pd.DataFrame(rows_display), use_container_width=True, hide_index=True)
        st.caption(f"{len(authors)} authors")
    else:
        st.info("No authors found yet.")


# ── Tab 5: Simulator ─────────────────────────────────────────────────────────

with tabs[4]:
    st.header("Simulator")
    st.caption("Preview how a URL or text would match topics and appear in a digest.")

    url_input = st.text_input("URL (optional — will fetch title)")
    text_input = st.text_area("Or paste raw text / title", height=100)

    if st.button("Run simulator", type="primary"):
        # Determine input text
        text_to_match = text_input.strip()

        if url_input.strip() and not text_to_match:
            with st.spinner("Fetching page title…"):
                try:
                    req = urllib.request.Request(
                        url_input.strip(),
                        headers={"User-Agent": "Mozilla/5.0 knowledge-os/1.0"},
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        html = resp.read(32768).decode("utf-8", errors="ignore")
                    import re
                    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
                    text_to_match = m.group(1).strip() if m else url_input.strip()
                    st.info(f"Using title: **{text_to_match}**")
                except Exception as e:
                    text_to_match = url_input.strip()
                    st.warning(f"Could not fetch title ({e}). Using URL as text.")

        if not text_to_match:
            st.warning("Enter a URL or some text to simulate.")
        else:
            with st.spinner("Running topic matcher…"):
                try:
                    matcher = get_topic_matcher()
                    story = {
                        "title": text_to_match,
                        "url": url_input.strip() or "https://example.com",
                        "score": 100,
                        "by": "simulator",
                        "id": 0,
                        "descendants": 0,
                        "time": datetime.now().timestamp(),
                        "fetched_at": datetime.now().isoformat(),
                        "source": "hackernews",
                    }
                    matched = matcher.match_stories([story])
                except Exception as e:
                    st.error(f"Matcher error: {e}")
                    matched = []

            if not matched:
                cfg_now = load_config()
                thresh = cfg_now["settings"]["similarity_threshold"]
                st.warning(
                    f"No topic matched above threshold ({thresh}). "
                    "This story would not appear in a digest."
                )
                # Still show scores
                try:
                    from match_topics import TopicMatcher
                    matcher2 = get_topic_matcher()
                    import numpy as np
                    story_emb = matcher2.model.encode([text_to_match])
                    all_scores = {}
                    for tname, temb in matcher2.topic_embeddings.items():
                        from sklearn.metrics.pairwise import cosine_similarity
                        s = cosine_similarity(story_emb, temb.reshape(1, -1))[0][0]
                        all_scores[tname] = float(s)
                    st.subheader("All topic scores (below threshold)")
                    st.bar_chart(pd.DataFrame.from_dict(all_scores, orient="index", columns=["score"]))
                except Exception:
                    pass
            else:
                m_story = matched[0]
                best_topic = m_story["matched_topic"]
                topic_score = m_story["topic_score"]
                all_scores = m_story["all_topic_scores"]

                c1, c2 = st.columns(2)
                c1.metric("Best topic", best_topic)
                c2.metric("Similarity score", f"{topic_score:.3f}")

                st.subheader("All topic scores")
                scores_df = pd.DataFrame.from_dict(all_scores, orient="index", columns=["score"])
                scores_df = scores_df.sort_values("score", ascending=False)
                st.bar_chart(scores_df)

                # Preview digest entry
                st.subheader("Digest preview")
                url_display = url_input.strip() or "https://example.com"
                digest_block = f"""\
*{best_topic}*

- [ ] {text_to_match}
  ↑100 | 0 comments | by simulator
  🔗 {url_display}
  Notes: """
                st.code(digest_block, language="markdown")
                st.markdown("---")
                st.markdown(f"**Rendered:**\n\n{digest_block}")
