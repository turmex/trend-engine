#!/usr/bin/env python3
"""
FormCoach Trend Engine — Personalized
=====================================
Sunday night cron → Monday morning email with:
  - Trend data (Google Trends, Reddit, Quora, Wikipedia)
  - News Headlines (via Google News RSS - Free)
  - PubMed studies (Scientific authority)
  - Lead Generation:
    - Local Leads (Bay Area/Sacramento pain discussions)
    - Executive/Founder Leads (Hacker News, r/fatFIRE, etc.)
  - AI-generated content strategy
"""

import os
import sys
import json
import time
import smtplib
import requests
import re
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION — PERSONALIZATION
# ═══════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# [PERSONALIZATION] Optimized Keyword Buckets
KEYWORDS = {
    "symptom": [
        "sciatica", "lower back pain", "neck pain", "anterior pelvic tilt",
        "stiff neck", "herniated disc", "cancer pain"
    ],
    "context": [
        "working from home", "standing desk", "office ergonomics", 
        "text neck", "driving back pain"
    ],
    "condition": [
        "fibromyalgia", "chronic pain syndrome", "degenerative disc disease",
        "work injury"
    ]
}

SUBREDDITS = {
    "pain_support": ["ChronicPain", "backpain", "Sciatica", "Fibromyalgia"],
    "fitness_recovery": ["flexibility", "posture", "bodyweightfitness", "PhysicalTherapy"],
}

# [NEW] Targeted Subreddits for Executives/Founders
EXEC_SUBREDDITS = [
    "fatFIRE",          # High Net Worth individuals/Early Retirees
    "startups",         # Founders
    "experienceddevs",  # Senior Tech Talent
    "consulting",       # Consultants (High travel/desk time)
    "sales",            # High stress/road warriors
    "ycombinator",      # Tech Founders
    "venturecapital"    # VCs
]

QUORA_SEARCH_QUERIES = [
    "best exercises for chronic back pain",
    "how to prevent lower back pain from sitting",
    "sciatica pain relief exercises",
    "posture correction for desk workers",
]

WIKI_ARTICLES = [
    "Chronic_pain", "Sciatica", "Fibromyalgia", "Low_back_pain", 
    "Physical_therapy", "Ergonomics", "Kyphosis"
]

# [PERSONALIZATION] Simple mapping of problem -> solution
TOPIC_SOLUTIONS = {
    "sciatica": ["Piriformis stretch", "Nerve flossing", "Figure-4 stretch"],
    "back pain": ["Cat-cow", "Bird dog", "McGill big 3"],
    "neck pain": ["Chin tucks", "Scalene stretch", "Thoracic extension"],
    "posture": ["Wall angels", "Band pull-aparts", "Doorway stretch"],
    "sitting": ["Hip flexor stretch", "Glute bridges", "Walking breaks"],
    "cancer pain": ["Gentle mobility", "Breathwork", "Mindful movement"], # Added for new topic
}

# ═══════════════════════════════════════════════════════════════════
# API CLIENTS & KEYS
# ═══════════════════════════════════════════════════════════════════

EMAIL_CONFIG = {
    "sender": os.getenv("SENDER_EMAIL", ""),
    "password": os.getenv("SENDER_PASSWORD", ""),
    "recipient": os.getenv("RECIPIENT_EMAIL", ""),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
}

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# NewsAPI removed in favor of RSS
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "FormCoachBot/1.0")

# ═══════════════════════════════════════════════════════════════════
# DATA COLLECTION MODULES
# ═══════════════════════════════════════════════════════════════════

def collect_google_trends(is_first_run: bool) -> dict | None:
    """Pull Google Trends data."""
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("  ⚠️  pytrends not installed")
        return None

    print("  Connecting to Google Trends...")
    # Add a random delay to avoid some rate limits
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    results = {}

    all_kw = [kw for group in KEYWORDS.values() for kw in group]
    batches = [all_kw[i : i + 5] for i in range(0, len(all_kw), 5)]
    timeframe = "today 3-m"

    for i, batch in enumerate(batches):
        try:
            print(f"  Batch {i + 1}/{len(batches)}: {batch}")
            pytrends.build_payload(batch, timeframe=timeframe, geo="US")
            iot = pytrends.interest_over_time()
            if iot is not None and not iot.empty:
                for kw in batch:
                    if kw in iot.columns:
                        vals = iot[kw].tolist()
                        results[kw] = {
                            "current": vals[-1] if vals else 0,
                            "prev_week": vals[-2] if len(vals) > 1 else 0,
                            "wow_pct": _pct_change(vals[-2] if len(vals) > 1 else 0, vals[-1] if vals else 0),
                            "4w_trend": _trend_direction(vals[-4:] if len(vals) >= 4 else vals),
                        }
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  Error on batch {batch}: {e}")
            time.sleep(5)
            # Try to continue with other batches

    return results if results else None

def collect_reddit() -> dict | None:
    """Pull top posts from Reddit."""
    try:
        import praw
    except ImportError:
        return None

    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("  ⚠️  Reddit credentials missing in .env")
        return None

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    results = {}
    for group, subs in SUBREDDITS.items():
        for sub_name in subs:
            try:
                print(f"  r/{sub_name}...")
                sub = reddit.subreddit(sub_name)
                posts = []
                for p in sub.top(time_filter="week", limit=10):
                    posts.append({
                        "title": p.title,
                        "score": p.score,
                        "comments": p.num_comments,
                        "url": f"https://reddit.com{p.permalink}",
                        "subreddit": sub_name,
                    })
                results[sub_name] = {"posts": posts}
            except Exception as e:
                print(f"  ⚠️  r/{sub_name} error: {e}")
    return results if results else None

def collect_local_leads() -> list | None:
    """Find potential leads in SF/Sacramento matching target profiles."""
    try:
        import praw
    except ImportError:
        return None

    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    print("  Fetching Executive/Local leads...")
    leads = []
    
    # [OPTIMIZED] 1. Search Location Subreddits (Broad Public)
    # Filter for high-intent keywords: "recommend", "doctor", "pt", "help"
    location_subs = "bayarea+sacramento+sanfrancisco+oakland+sanjose+SiliconValley"
    pain_query = '("back pain" OR sciatica OR "neck pain" OR "work injury" OR "car accident") AND (recommend OR doctor OR pt OR chiropractor OR help)'
    
    try:
        for post in reddit.subreddit(location_subs).search(pain_query, sort="new", time_filter="month", limit=10):
            leads.append({
                "source": f"r/{post.subreddit}",
                "title": post.title,
                "url": f"https://reddit.com{post.permalink}",
                "snippet": (post.selftext[:200] + "...") if post.selftext else "No content",
                "type": "Local Help Request 📍"
            })
    except Exception as e:
        print(f"  ⚠️  Local search error: {e}")

    # [OPTIMIZED] 2. Search Executive/Founder Subreddits (Specific Target Profile)
    # Combining the NEW list of subs
    exec_subs_str = "+".join(EXEC_SUBREDDITS)
    # Search for LIFESTYLE CAUSES (desk, chair, travel) + PAIN
    exec_query = '("pain" OR "posture" OR "herniated" OR "sore") AND ("desk" OR "computer" OR "travel" OR "flight" OR "chair" OR "office")'
    
    try:
        for post in reddit.subreddit(exec_subs_str).search(exec_query, sort="new", time_filter="month", limit=10):
            leads.append({
                "source": f"r/{post.subreddit}",
                "title": post.title,
                "url": f"https://reddit.com{post.permalink}",
                "snippet": (post.selftext[:200] + "...") if post.selftext else "No content",
                "type": "EXEC LIFESTYLE PAIN 🎯"
            })
    except Exception as e:
        print(f"  ⚠️  Exec search error: {e}")

    return leads

def collect_hacker_news_leads() -> list | None:
    """Fetch recent Hacker News discussions about ergonomics/pain."""
    print("  Fetching Hacker News leads...")
    leads = []
    
    # Using Algolia API for Hacker News (Free, No Auth)
    url = "http://hn.algolia.com/api/v1/search_by_date"
    # [OPTIMIZED] Queries targeting tech lifestyle
    queries = ["standing desk", "office chair", "back pain", "RSI", "posture", "carpal tunnel"]
    
    for q in queries:
        try:
            params = {
                "query": q,
                "tags": "story", # or 'comment'
                "hitsPerPage": 5,
                "numericFilters": f"created_at_i>{int(time.time() - 604800)}" # Last 7 days
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            for hit in data.get("hits", []):
                leads.append({
                    "source": "Hacker News",
                    "title": hit.get("title", ""),
                    "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "snippet": "Tech/Founder Community Discussion",
                    "type": "TECH LEADER MATCH 🚀"
                })
        except Exception as e:
            print(f"  ⚠️  HN search error for {q}: {e}")
            
    # Deduplicate by URL
    seen = set()
    unique_leads = []
    for l in leads:
        if l['url'] not in seen:
            seen.add(l['url'])
            unique_leads.append(l)
            
    return unique_leads[:10]

def collect_pubmed() -> list | None:
    """Fetch recent scientific studies on chronic pain/rehab."""
    try:
        from Bio import Entrez
        Entrez.email = EMAIL_CONFIG["sender"] or "test@example.com"
    except ImportError:
        print("  ⚠️  biopython not installed")
        return None

    print("  Fetching PubMed studies...")
    studies = []
    # [OPTIMIZED] Search for Title/Abstract specific matches
    # Ensures relevance (paper IS about pain management), not just random mention
    query = """
    ("chronic pain"[Title/Abstract] OR "cancer pain"[Title/Abstract] OR "sciatica"[Title/Abstract] OR "low back pain"[Title/Abstract] OR "neck pain"[Title/Abstract]) 
    AND 
    ("exercise"[Title/Abstract] OR "rehabilitation"[Title/Abstract] OR "physical therapy"[Title/Abstract] OR "ergonomics"[Title/Abstract])
    AND "last 1 year"[dp]
    """
    
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=5, sort="date")
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record["IdList"]
        if id_list:
            handle = Entrez.esummary(db="pubmed", id=",".join(id_list))
            summaries = Entrez.read(handle)
            handle.close()
            
            for doc in summaries:
                studies.append({
                    "title": doc.get("Title", ""),
                    "journal": doc.get("Source", ""),
                    "date": doc.get("PubDate", ""),
                    "id": doc.get("Id", "")
                })
    except Exception as e:
        print(f"  ⚠️  PubMed error: {e}")
        
    return studies

def collect_rss_news() -> list | None:
    """Fetch news from Google News RSS (Free & reliable)."""
    print("  Fetching Google News RSS...")
    
    # [OPTIMIZED] Bulletproof Boolean Query
    # (Condition) AND (Context/Solution)
    # This filters out general noise and focuses on actionable news
    query_str = '("back pain" OR "neck pain" OR "sciatica" OR "cancer pain" OR "pelvic tilt" OR "chronic pain") AND ("treatment" OR "exercise" OR "study" OR "ergonomics" OR "posture" OR "work injury" OR "prevention") when:7d'
    q = urllib.parse.quote(query_str)
    rss_url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(rss_url)
        articles = []
        for entry in feed.entries[:7]: # Top 7
            articles.append({
                "title": entry.title,
                "source": entry.source.title if hasattr(entry, 'source') else "Google News",
                "url": entry.link,
                "date": entry.published[:16] if hasattr(entry, 'published') else "Recent"
            })
        return articles
    except Exception as e:
        print(f"  ⚠️  RSS error: {e}")
        return None

def collect_scrapling_forums() -> list | None:
    """Use Scrapling to fetch discussions from a target site (example placeholder)."""
    # This is a template for adding robust scraping of specific forums
    return [] 

# ═══════════════════════════════════════════════════════════════════
# ANALYSIS & STRATEGY
# ═══════════════════════════════════════════════════════════════════

def _pct_change(old, new):
    if old == 0: return 0.0
    return round((new - old) / old * 100, 1)

def _trend_direction(values):
    if len(values) < 2: return "stable"
    first = sum(values[:len(values)//2]) / max(1, len(values)//2)
    second = sum(values[len(values)//2:]) / max(1, len(values)-len(values)//2)
    if first == 0: return "stable"
    pct = (second - first) / first * 100
    if pct > 20: return "rising"
    return "stable"

def build_analysis(google, reddit, pubmed, news, leads, hn_leads):
    analysis = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "theme": "General Pain Management", # Default
        "top_mover": None,
        "google": google,
        "reddit": reddit,
        "pubmed": pubmed,
        "news": news,
        "leads": leads,
        "hn_leads": hn_leads
    }
    
    # Determine theme from top google mover
    if google:
        sorted_kw = sorted(
            [(k, v) for k, v in google.items()], 
            key=lambda x: x[1]['wow_pct'], 
            reverse=True
        )
        if sorted_kw:
            top = sorted_kw[0]
            analysis["top_mover"] = {"keyword": top[0], **top[1]}
            if top[1]['wow_pct'] > 5:
                # Update theme if significant mover found
                analysis["theme"] = top[0]
                
    return analysis

def generate_content_strategy_llm(analysis: dict):
    if not ANTHROPIC_API_KEY:
        return None
        
    theme = analysis["theme"]
    
    # Construct context string
    pubmed_txt = "\n".join([f"- STUDY: {s['title']} ({s['journal']})" for s in (analysis['pubmed'] or [])[:3]])
    news_txt = "\n".join([f"- NEWS: {n['title']} ({n['source']})" for n in (analysis['news'] or [])[:3]])
    
    prompt = f"""
    You are a content strategist for an expert Pain Management Coach.
    
    DATA THIS WEEK:
    Theme: {theme}
    Top Mover: {analysis.get('top_mover', {}).get('keyword', 'N/A')} (+{analysis.get('top_mover', {}).get('wow_pct', 0)}%)
    
    SCIENTIFIC BACKING (PubMed):
    {pubmed_txt}
    
    MAINSTREAM CONTEXT (News):
    {news_txt}
    
    Generate a JSON content plan with:
    1. "theme_narrative": Why this matters now.
    2. "video_idea": Title, Hook, Exercises (from {TOPIC_SOLUTIONS.get(theme, [])}).
    3. "authority_post": A LinkedIn/Blog post concept citing one of the studies.
    """
    
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-3-sonnet-20240229", "max_tokens": 1000, "messages": [{"role": "user", "content": prompt}]}
        )
        if resp.status_code == 200:
            content = resp.json()['content'][0]['text']
            # Basic cleanup to ensure we get JSON (in production, use a parser)
            return content 
    except Exception as e:
        print(f"LLM Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════
# DATA PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

def get_latest_snapshot() -> dict | None:
    """Load the most recent prior data snapshot."""
    files = sorted(DATA_DIR.glob("snapshot_*.json"), reverse=True)
    if not files: return None
    with open(files[0]) as f: return json.load(f)

def save_snapshot(data: dict):
    """Save this week's data."""
    ts = datetime.now().strftime("%Y-%m-%d")
    with open(DATA_DIR / f"snapshot_{ts}.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

# ═══════════════════════════════════════════════════════════════════
# EMAIL & MAIN
# ═══════════════════════════════════════════════════════════════════

def send_email(html, recipient):
    """Send the HTML email to the recipient."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Trend Brief: {datetime.now().strftime('%b %d')}"
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))
    
    try:
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.send_message(msg)
        print("  ✅ Email sent!")
    except Exception as e:
        print(f"  ❌ Email failed: {e}")

def main():
    print("--- Starting Trend Engine ---")
    
    # 1. Load History
    prior = get_latest_snapshot()
    if prior:
        print(f"  Found prior snapshot from {prior.get('date', 'unknown')}")
    
    # 2. Collect Data
    google = collect_google_trends(is_first_run=prior is None)
    reddit = collect_reddit()
    pubmed = collect_pubmed()
    # news = collect_news() # Removed NewsAPI
    news = collect_rss_news() # Replaced with RSS
    leads = collect_local_leads()
    hn_leads = collect_hacker_news_leads()
    
    # 3. Analyze
    analysis = build_analysis(google, reddit, pubmed, news, leads, hn_leads)
    strategy = generate_content_strategy_llm(analysis)
    
    # 4. Save Snapshot for Next Week
    save_snapshot({
        "date": analysis["date"],
        "google": google,
        "reddit": reddit,
        "pubmed": pubmed,
        "news": news,
        "leads": leads,
        "hn_leads": hn_leads
    })
    
    # 5. Build HTML (Enhanced)
    html = f"""
    <html><body style="font-family:sans-serif;color:#333;">
    <div style="max-width:600px;margin:auto;">
        <h1 style="color:#2c3e50;">Trend Brief: {analysis['theme'].title()}</h1>
        <p style="background:#f0f9ff;padding:10px;border-left:4px solid #3498db;">
            <strong>Top Mover:</strong> {analysis.get('top_mover', {}).get('keyword')} 
            <span style="color:{'green' if analysis.get('top_mover', {}).get('wow_pct', 0) > 0 else 'red'}">
            ({analysis.get('top_mover', {}).get('wow_pct')}% vs last week)
            </span>
        </p>
        
        <h2 style="border-bottom:2px solid #eee;padding-bottom:5px;">🧬 PubMed Science & Prevention</h2>
        <ul style="padding-left:20px;">
        {''.join([f"<li style='margin-bottom:8px;'><strong>{s['title']}</strong><br><span style='color:#7f8c8d;font-size:0.9em;'>{s['journal']} • {s['date']}</span></li>" for s in (pubmed or [])])}
        </ul>
        
        <h2 style="border-bottom:2px solid #eee;padding-bottom:5px;">📰 News Context (Google RSS)</h2>
        <ul style="padding-left:20px;">
        {''.join([f"<li style='margin-bottom:8px;'><a href='{n['url']}' style='color:#2980b9;text-decoration:none;'>{n['title']}</a><br><span style='color:#7f8c8d;font-size:0.9em;'>{n['source']}</span></li>" for n in (news or [])])}
        </ul>
        
        <h2 style="border-bottom:2px solid #eee;padding-bottom:5px;">🤖 AI Content Strategy</h2>
        <div style="background:#fef9e7;padding:15px;border-radius:5px;">
            <pre style="white-space:pre-wrap;font-family:inherit;">{strategy if strategy else "Add ANTHROPIC_API_KEY to generate strategy."}</pre>
        </div>
        
        <h2 style="border-bottom:2px solid #eee;padding-bottom:5px;">📍 Local Leads (Bay Area / Sac) & Founder Profiles</h2>
        <div style="background:#e8f8f5;padding:15px;border-radius:5px;">
            <p style="font-size:0.9em;color:#555;">Potential clients discussing pain in your area:</p>
            <ul style="padding-left:20px;">
            {''.join([f"<li style='margin-bottom:10px;'><strong><a href='{l['url']}' style='color:#16a085;text-decoration:none;'>{l['title']}</a></strong><br><span style='color:#7f8c8d;font-size:0.8em;'>{l['source']} • {l['type']}</span><br><span style='font-size:0.8em;'>{l['snippet']}</span></li>" for l in (leads or [])])}
            </ul>
        </div>
        
        <h2 style="border-bottom:2px solid #eee;padding-bottom:5px;">🚀 Executive / Tech Leader Leads (HN)</h2>
        <div style="background:#fff0f0;padding:15px;border-radius:5px;">
            <p style="font-size:0.9em;color:#555;">Tech founders & VCs discussing ergonomics right now:</p>
            <ul style="padding-left:20px;">
            {''.join([f"<li style='margin-bottom:10px;'><strong><a href='{l['url']}' style='color:#c0392b;text-decoration:none;'>{l['title']}</a></strong><br><span style='color:#7f8c8d;font-size:0.8em;'>{l['source']} • {l['type']}</span></li>" for l in (hn_leads or [])])}
            </ul>
        </div>
        
        <p style="color:#95a5a6;font-size:0.8em;margin-top:30px;text-align:center;">
            Generated by FormCoach Trend Engine • {analysis['date']}
        </p>
    </div>
    </body></html>
    """
    
    if "--preview" in sys.argv:
        print(html)
    else:
        # Only send email if recipients are configured
        if EMAIL_CONFIG["recipient"]:
            send_email(html, EMAIL_CONFIG["recipient"])
        else:
            print("  ⚠️  No recipient configured. Skipping email.")

if __name__ == "__main__":
    main()
