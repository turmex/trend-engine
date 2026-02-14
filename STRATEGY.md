# FormCoach Content Flywheel — V1 MVP
## Strategy, SEO, AI Findability & Implementation Guide

---

## What the MVP Delivers

A Python script on a Sunday night cron job. It collects trend data from four sources, compares to last week's stored snapshot, detects genuinely new emerging signals, calls Claude API once to generate a complete content playbook, and sends Bart one email with everything he needs for the week:

1. **Weekly Trend Data** — Google Trends, Reddit, Quora, Wikipedia pageviews
2. **Week-over-Week Deltas** — What changed since last run (first run shows month baseline)
3. **Emerging Signal Detection** — New rising queries, new Reddit conversation topics, Wikipedia breakouts, and new Quora questions that didn't exist last week. These are the most valuable signals — topics nobody else is covering yet.
4. **AI-Generated Content Strategy** — Specific scripts, captions, and posting instructions for Monday, Wednesday, Friday across every platform, informed by both established trends AND emerging signals
5. **5 Engagement Opportunities** — Reddit/Quora posts where Bart should reply to build authority

One email. One Claude API call. Everything Bart needs. ~3 hours/week to execute.

---

## The Content Chain — Why This Sequence

### Monday → Wednesday → Friday Logic

```
SUNDAY NIGHT
  Pipeline: scrape → compare → Claude API → email
       ↓
MONDAY — VIDEO (The Hook)
  3-5 min exercise routine addressing the week's trending topic
  → YouTube, LinkedIn, IG Reels, TikTok, Facebook
  → Comments pour in: "I have this exact problem" / "Does this work for X?"
  → YouTube starts indexing the video for search
       ↓
WEDNESDAY — LINKEDIN POST + BLOG (The Depth)
  Long-form text referencing Monday's video AND comment themes
  → LinkedIn (primary), blog (SEO anchor), Medium, Substack
  → Drives second wave of video views
  → Blog article gets crawled by Google and AI training pipelines
  → Establishes Bart as the data-informed clinical expert
       ↓
FRIDAY — SOCIAL CARD + RESULTS ASK (The Close)
  One data stat + one tip + "How did Monday's exercises feel?"
  → LinkedIn, IG, X/Twitter, Pinterest, Facebook
  → User replies = outcomes data
  → Closes the weekly loop, feeds next Sunday's pipeline
       ↓
NEXT SUNDAY
  Pipeline picks up new trend data + THIS week's engagement signals
  → Brief incorporates audience feedback into next week's theme
  → Cycle accelerates with every revolution
```

**Why video on Monday, not Tuesday or Wednesday:**
- Monday morning = "I need to fix myself" mindset after a weekend of sitting
- Video generates the richest engagement data (comments with real pain descriptions)
- 48 hours of comment accumulation gives Wednesday's post raw material
- YouTube needs upload-to-index time; Monday upload = showing in search by midweek

**Why text on Wednesday, not Tuesday:**
- Monday's video needs time to accumulate comments that Wednesday references
- Wednesday is peak LinkedIn engagement (midweek, lunch-break scrolling)
- "Monday I shared X. Many of you mentioned Y. Here's what's happening..." creates narrative continuity

**Why social card on Friday:**
- Lightweight format for end-of-week attention spans
- The "did you try it?" ask is timed for when people have had 4 days with the exercises
- Friday replies become data for next week's pipeline

### The Self-Feeding Cycle

Each week's content literally produces the raw material for next week:

| This Week's Output | Feeds Into |
|---|---|
| Monday video comments | Wednesday post ("many of you mentioned...") |
| Wednesday engagement | Friday follow-up context |
| Friday results replies | Next week's brief ("last week your audience reported...") |
| All platform engagement | Next week's theme selection + Claude prompt |
| Blog article | Long-term SEO, AI training data |
| Reddit/Quora replies | Bart's authority + future engagement opps |

After 4-6 weeks, the flywheel is self-sustaining. After 12 weeks, it's a moat.

---

## Emerging Signal Detection — Finding What's New, Not Just What's Moving

Tracking week-over-week deltas on fixed keywords tells you "sciatica went up 15%." That's useful. But the higher-value intelligence is detecting signals that **didn't exist last week at all** — a new rising query, a Reddit conversation on a topic nobody was discussing, a Wikipedia article that suddenly spiked from nowhere. These represent untapped content opportunities where Bart can be the **first authoritative voice**, before any competitor notices.

### What the System Detects

**New Rising Search Queries:** Google Trends surfaces "rising queries" — related searches that are gaining momentum. The system stores every rising query in each weekly snapshot, then diffs against the prior week. If "sciatica driving commute" appears this week but wasn't in last week's rising queries, that's a new signal. These often foreshadow the *next* trending keyword — catching them early means Bart creates content on a topic 1-2 weeks before it peaks.

**New Reddit Conversation Topics:** The system fingerprints each week's Reddit posts by extracting significant topic words from titles. When a post appears with keywords that weren't in last week's fingerprint — like "dowager hump" or "decompression therapy" — that's a new conversation emerging. These get flagged with their novel terms highlighted so Bart can see exactly what's new.

**Wikipedia Breakouts:** Wikipedia pageviews are a clean proxy for "people actively researching a health condition." The system flags any article with >15% WoW spike AND compares against the prior snapshot's daily averages. If Kyphosis goes from 800/day to 1,400/day in a week, something triggered public attention — maybe a viral TikTok, a celebrity diagnosis, or a news article. Bart can ride that wave.

**New Quora Questions:** Questions appearing on Quora this week that weren't in last week's snapshot. These represent people actively seeking answers — each one is both a content idea and an engagement opportunity.

**Reddit Post Deduplication:** Every Reddit post is tagged as "NEW" or returning from last week. This prevents Bart from seeing the same viral post week after week and ensures engagement opportunities are genuinely fresh conversations.

### How Emerging Signals Flow into the Content Strategy

The emerging signals are passed directly into the Claude API prompt alongside the standard trend data. The prompt instructs Claude to prioritize emerging signals because:

1. **Less competition** — nobody else is creating content on a topic that just emerged
2. **Higher novelty** — audiences reward creators who cover new things first
3. **SEO opportunity** — blog articles targeting emerging long-tail queries can rank quickly before competition builds
4. **AI findability** — being the first authoritative source on an emerging topic means LLMs are more likely to cite your content as the reference

### Example Scenario

Week 4's brief shows: "lower back pain" is the established theme (+8% WoW, stable). But the emerging signals section reveals:
- New rising query: "lower back pain RTO" (return-to-office related)
- New Reddit thread: "Sciatica flare-ups returning to office — anyone else?" (▲298, 87 comments)
- Wikipedia: Kyphosis pageviews up 58% (unusual spike)

The Claude API takes all of this and generates Monday's video angle not as generic "lower back pain exercises" but as **"Your Back Pain Is Worse Because You're Back in the Office — Here's the Fix"** — directly addressing the emerging RTO signal. That's a video that resonates with a specific moment rather than being timeless-but-generic. The emerging signals make the content topical and urgent.

---

## Multi-Platform Recycling: 15 Pieces from 2 Creation Acts

Bart creates two things per week. Everything else is reformatting.

### Primary Asset #1: Monday Video (30-45 min to record)

| Platform | Format | How | Extra Time |
|---|---|---|---|
| **YouTube** | Full 3-5 min | Upload. SEO title, description (with timestamps + blog link), tags. | 10 min |
| **LinkedIn** | Native video | Same file, shorter caption — provocative data stat as hook. | 5 min |
| **IG Reels** | 60-90 sec | Cut best 1-2 exercises. Vertical crop. Text overlay. Hook in 3 sec. | 15 min |
| **TikTok** | Same as IG | Identical file, casual caption, trending sounds optional. | 5 min |
| **Facebook** | Same as LinkedIn | Cross-post. Also post to relevant FB groups. | 5 min |

### Primary Asset #2: Wednesday LinkedIn Post (30-45 min to write)

| Platform | Format | How | Extra Time |
|---|---|---|---|
| **LinkedIn** | 300-600 word post | Primary creation. References Monday video + comments. | 0 (primary) |
| **Blog** (bartonfirch.com) | 800-1200 word article | Expand LinkedIn post. Add headers, images, schema markup, internal links. | 20 min |
| **Medium** | Cross-post | Same as blog. Canonical URL → bartonfirch.com. | 5 min |
| **Substack** | Newsletter excerpt | Condensed version + link. Becomes "The Pulse" newsletter lead. | 10 min |

### Friday Social Card (10 min to approve — David auto-generates from brief data)

| Platform | Format | Extra Time |
|---|---|---|
| **LinkedIn** | Image + caption + CTA | 5 min |
| **Instagram** | Same image + Stories poll | 5 min |
| **X/Twitter** | Image + thread format | 5 min |
| **Pinterest** | Tall infographic pin | 10 min |
| **Facebook** | Same as LinkedIn | 2 min |

### Weekly Totals

| Metric | Count |
|---|---|
| Bart's creation time | ~3 hours |
| Platforms reached | 8 (YouTube, LinkedIn, IG, TikTok, FB, blog, Medium, Pinterest) |
| Total content pieces | 13-15 |
| Evergreen SEO assets | 2 (YouTube video + blog article) |

---

## SEO Strategy — Making Content Rank

### The Blog as SEO Engine

Every Wednesday LinkedIn post expands into a blog article. Each article:

**Targets a specific long-tail keyword** from the trend data. Not "back pain" (too competitive) but "piriformis stretch for desk workers" or "sciatica exercises for long commutes." The brief's `seo_notes.target_keyword` tells Bart exactly what to target.

**Includes original data nobody else has.** "Our analysis of Google search trends shows sciatica interest up 28% this month, with 'sciatica while sitting' as the fastest-rising related query." No competitor has this because nobody else is running a trend pipeline against fitness data.

**Uses schema markup** (included in the brief's SEO notes):
- `HowTo` schema for exercise routines → appears as step-by-step in Google results
- `FAQPage` schema for Q&A sections → wins FAQ rich snippets
- `Person` schema for Bart → builds entity recognition in Google's Knowledge Graph
- `VideoObject` schema linking to YouTube → video carousel in search results

**Builds topical authority clusters** through internal linking. Each article links to 2-3 previous related articles: "If your sciatica is caused by anterior pelvic tilt, see our [APT correction guide](/anterior-pelvic-tilt-exercises)." After 12 weeks, you have 12 interlinked articles forming a topical cluster around posture/pain.

### YouTube as the Second Search Engine

YouTube is the #2 search engine globally. Monday videos do double duty: social engagement AND search ranking.

The brief includes YouTube-specific SEO in every Monday section:
- **Title format:** "[Problem] — [Number] Exercises That Actually Work ([Year])"
- **Description:** First 2 lines keyword-rich (they show in search), then timestamps, then blog link
- **Tags:** 8-10 mixing broad ("back pain exercises") and specific ("piriformis stretch sitting")
- **Thumbnail:** Bart demonstrating the exercise with text overlay showing the problem

### Pinterest as Long-Tail Discovery

Most fitness creators ignore Pinterest. That's an opportunity. Pinterest pins have a half-life of **months** — a pin you create today surfaces in search 6+ months later. The Friday social card, reformatted as a tall vertical pin with keyword-rich description, creates a persistent discovery channel.

### Compounding SEO Timeline

| Week | SEO State |
|---|---|
| 1-4 | Blog articles indexed. YouTube videos ranking for long-tail. |
| 5-8 | Internal link network forming. Topical authority emerging. |
| 9-12 | Multiple articles ranking. YouTube channel authority growing. Pinterest pins surfacing. |
| 13-26 | Topical authority established. Competing for medium-tail keywords. AI models starting to cite content. |
| 27-52 | Moat. 50+ indexed articles, 50+ YouTube videos. First page results for dozens of long-tail queries. |

---

## AI & LLM Findability — Getting Cited by AI Models

This is the emerging frontier. When someone asks ChatGPT or Claude "how do I fix sciatica from sitting all day," you want Bart's content in the answer. Here's how:

### How AI Models Find and Cite Content

1. **Training data** — Models learn from web crawls. Blog articles with clear, authoritative, well-structured text get absorbed into training data.

2. **Retrieval (RAG/search)** — Models with web search (like Claude, Perplexity, ChatGPT with browsing) pull from search results in real-time. If your blog ranks on Google, it gets cited by AI.

3. **Entity recognition** — If Bart Firch becomes a recognized entity (person + expertise + body of work), models learn to associate his name with fitness expertise.

### Tactical Moves for AI Findability

**Structure content as Q&A.** AI models love extracting clean question-answer pairs. Every blog article should include:
```
## What causes [condition]?
[Direct, authoritative 2-3 sentence answer.]

## What are the best exercises for [condition]?
[Numbered list with clear descriptions.]
```

**Write definitive statements.** LLMs prefer to cite content that makes clear claims:
- ✅ "The primary cause of sciatica in desk workers is piriformis compression of the sciatic nerve, exacerbated by prolonged hip flexion."
- ❌ "Sciatica can be caused by many things and you should see a doctor."

The first version gets quoted by AI. The second gets ignored.

**Use original data as citation bait.** "According to our analysis of 12 weeks of Google Trends data, sciatica searches peak in January and September, correlating with return-to-office and post-summer patterns." This is the kind of claim AI models pick up and cite because it's unique, specific, and data-backed.

**Build entity authority.** Every article includes an author bio with structured Person schema. Cross-references between blog, YouTube, LinkedIn, and Medium reinforce that Bart Firch = fitness/posture/pain expertise. Over time, AI models learn this association.

**Publish consistently.** AI training data crawls are periodic. Consistent weekly publishing means more of your content appears in each crawl cycle. After 6 months, your site has 26 articles covering 26 pain/posture topics — the density signals authority.

**Include timestamps and dates.** AI models with search capabilities prioritize recent content. Dating your articles and including "Updated [month] [year]" signals freshness.

### The AI Findability Flywheel

```
Trend data reveals what people are searching for
  → Blog article directly answers those queries with original data
    → Google ranks the article (traditional SEO)
      → AI models with web search cite the article (AI findability)
        → AI citations drive more traffic → more backlinks → better Google ranking
          → Better ranking → more AI citations → cycle compounds
```

This is why the blog (not just LinkedIn) matters. LinkedIn posts don't get crawled by AI training pipelines. Blog articles on bartonfirch.com do.

---

## Engagement Opportunities — V1 Lead Gen

The brief surfaces 5 Reddit/Quora posts where someone is actively seeking help. Selection criteria:
- Contains help-seeking signals: "advice," "struggling," "months/years," "nothing works"
- Posted in the past 7 days (fresh conversation)
- Enough comments/votes to indicate others share the problem
- From a subreddit relevant to Bart's expertise

**Bart's approach:** Reply with genuine help. No pitch. No link. Just a thoughtful 3-4 sentence response drawing on clinical experience. Example:

> "What you're describing sounds like piriformis-driven sciatica, which is extremely common in people who sit 8+ hours. The nerve gets compressed where it passes through (or sometimes under) the piriformis muscle. Try this: figure-4 stretch, 30 seconds each side, 3x/day for a week. If the pain centralizes or decreases, that confirms the mechanism."

This does three things:
1. **Builds Bart's Reddit/Quora authority** — his profile accumulates helpful answers
2. **Creates natural backlinks** if he later adds a blog link after establishing credibility
3. **Surfaces potential clients** — some of these people will click his profile, find his content, and eventually become subscribers or clients

### V2: Formal Lead Scoring (Future)

In V2, we add:
- **X/Twitter API** — monitor tweets mentioning pain/posture keywords, surface tweeters who fit client profile
- **Engagement scoring** — weight leads by: geographic proximity to Bart, language suggesting purchasing intent ("looking for a trainer"), severity of problem, platform engagement level
- **Separate Tuesday email** — "5 Qualified Leads This Week" with scored profiles and suggested outreach messages
- **CRM integration** — track which leads Bart engaged, outcomes, conversion to consultations

But V1 is just: here are 5 people who need help. Your call if you want to reply.

---

## Technical Implementation — Step by Step

### Prerequisites

- Python 3.10+
- Gmail account with App Password enabled
- Reddit API credentials (free)
- Claude API key (for AI-generated strategy — optional, falls back to templates)

### Step 1: Setup (15 min)

```bash
git clone [repo] && cd fc-engine
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Step 2: First Test Run (5 min)

```bash
# Terminal preview only — no email sent, no data collected
python trend_engine.py --preview --skip-google --skip-reddit --skip-quora
```

This runs with empty data to verify the script works. You'll see the template-based strategy with placeholder data.

### Step 3: First Real Run with Data (10 min)

```bash
# Collect real data, show preview
python trend_engine.py --preview
```

This pulls live Google Trends, Reddit, Quora, and Wikipedia data. The first run has no prior snapshot, so it shows baseline data without deltas. Review the output.

### Step 4: Test Email Delivery (5 min)

```bash
# Send to yourself first
# (temporarily set RECIPIENT_EMAIL to your own email in .env)
python trend_engine.py
```

Check your inbox. Verify HTML renders correctly in your email client.

### Step 5: Schedule the Cron Job (5 min)

```bash
crontab -e

# Add: Run every Sunday at 5am
0 5 * * 0 cd /absolute/path/to/fc-engine && /absolute/path/to/venv/bin/python trend_engine.py >> /absolute/path/to/fc-engine/cron.log 2>&1
```

For macOS, alternative using launchd:
```bash
# Or just set a Sunday night recurring reminder and run manually
# until you trust the output
```

### Step 6: Second Run Verification

After the first run saves a snapshot to `data/snapshot_YYYY-MM-DD.json`, the second run will automatically detect it and compute week-over-week deltas. Run manually after a week (or immediately for testing — the deltas will be zero but the mechanism works).

### Step 7: Iterate with Bart

Send Bart the first brief. His feedback shapes everything:
- "I don't care about Quora" → remove Quora section
- "Can you add yoga-specific subreddits?" → add subreddits
- "The exercise suggestions are off" → Bart refines the EXERCISE_RX mapping
- "The video script needs to be shorter" → adjust the Claude prompt
- "I want the blog post pre-written" → add blog draft to Claude prompt output

---

## First Run vs. Subsequent Runs

### First Run (Baseline)

Since there's no prior snapshot:
- Google Trends shows 3-month trailing data with 4-week and 12-week averages
- No "vs last run" deltas (column hidden)
- The email banner says "🎉 First Run — Baseline Report"
- Data is saved as the first snapshot in `data/`

### Subsequent Runs (Deltas)

With a prior snapshot available:
- Each Google Trends keyword shows a "vs last run" delta in addition to standard WoW
- Theme selection considers prior week's theme for narrative continuity
- The Claude prompt includes last week's theme so it can write transition language
- Reddit/Quora data shows fresh posts (not repeat from last week)

### Data Storage

Each run saves a JSON snapshot to `data/snapshot_YYYY-MM-DD.json`. This accumulates over time, enabling:
- Historical trend analysis
- Monthly/quarterly report generation (V2)
- Pattern detection (seasonal spikes)
- Product roadmap decisions (which exercises to build into FormCoach app)

---

## Cost

| Item | V1 Cost |
|---|---|
| Google Trends (pytrends) | Free |
| Reddit API (PRAW) | Free |
| Quora (Google scraping) | Free |
| Wikipedia API | Free |
| Claude API (1 call/week) | ~$0.10-0.25/week (~$1-4/month) |
| Gmail SMTP | Free |
| **Total** | **~$1-4/month** |

---

## V1 → V2 Roadmap

### V1 (Current): Weekly Email to Bart
- [x] Google Trends collection + WoW deltas
- [x] Reddit monitoring (13 subreddits) with NEW/returning post tagging
- [x] Quora question discovery
- [x] Wikipedia pageview tracking
- [x] Week-over-week snapshot comparison
- [x] **Emerging signal detection** — new rising queries, new Reddit topics, Wikipedia breakouts, new Quora questions
- [x] Reddit post deduplication across weeks
- [x] Claude API content strategy generation (with emerging signals in prompt)
- [x] Platform-by-platform posting instructions
- [x] 5 engagement opportunities
- [x] HTML email delivery
- [x] Cron automation
- [x] Graceful degradation (theme falls back to Wikipedia/Reddit if Google Trends fails)

### V2: Lead Scoring + X/Twitter
- [ ] X/Twitter API integration for tweet monitoring
- [ ] Lead scoring model (geo, intent, severity, platform)
- [ ] Separate Tuesday "Leads" email
- [ ] Auto-generated social cards (Pillow/matplotlib from the Friday data)
- [ ] Comment sentiment analysis on Bart's posts (feed into next brief)
- [ ] Monthly trend recap auto-generation

### V3: Platform
- [ ] Web dashboard showing trend history
- [ ] Multi-creator support (other fitness experts get their own briefs)
- [ ] Auto-draft full blog posts from trend data
- [ ] Quarterly "State of Pain & Posture" report (gated for email capture)
- [ ] Integration with FormCoach app (trending exercises surfaced in-product)
- [ ] RSS-to-social automation (blog → auto-post to platforms)

---

## Bart's Weekly Time Commitment

| Activity | Time | When |
|---|---|---|
| Read Trend Brief | 10 min | Monday morning |
| Record video | 30-45 min | Monday |
| Upload/reformat to 5 platforms | 30-40 min | Monday |
| Write LinkedIn post (draft in brief) | 30-45 min | Wednesday |
| Expand to blog article | 20 min | Wednesday |
| Cross-post to Medium | 5 min | Wednesday |
| Review/post Friday social card | 10 min | Friday |
| Reply to 2-3 engagement opps | 15 min | Whenever |
| **Total** | **~2.5-3 hours/week** | |

The Trend Brief eliminates the hardest part of content creation: deciding **what** to create. Bart's time is spent executing, not researching or strategizing. The pipeline handles the thinking. Bart brings the 15K hours of clinical expertise.
