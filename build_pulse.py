#!/usr/bin/env python3
"""
Lionpoint Partners - Market Pulse site generator.
Parses daily Market Pulse scripts (.md) into SEO-optimized article pages,
builds the Market Pulse hub, sitemap.xml, robots.txt, RSS feed, and injects
SEO tags + nav link into the homepage.

Usage: python3 build_pulse.py --scripts <dir> --repo <dir>
Idempotent: safe to re-run; regenerates all derived files.
"""
import re, os, glob, html, json, argparse, datetime

DOMAIN = "https://lionpointpartners.com"
SITE = "Lionpoint Partners"
LOGO = DOMAIN + "/icon-512.png"  # generated below

MONTHS = ["January","February","March","April","May","June","July",
          "August","September","October","November","December"]

# ---------- parsing ----------
SIGNOFF_MARKERS = ["my inbox","inbox is","quietly weighing","weighing your options",
    "weigh your options","weighing a move","reach out","drop me a line","happy to chat",
    "that's the read","thats the read","that's the rundown","thats the rundown",
    "back tomorrow","more tomorrow","see you tomorrow"]

def scrub_signoff(p):
    sents = re.split(r"(?<=[.!?])\s+", p)
    kept = [x for x in sents if not any(m in x.lower() for m in SIGNOFF_MARKERS)]
    return " ".join(kept).strip()

def split_sections(md):
    secs = {}
    cur = "_pre"; buf = []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.*)", line)
        if m:
            secs[cur] = "\n".join(buf).strip(); cur = m.group(1).strip(); buf = []
        else:
            buf.append(line)
    secs[cur] = "\n".join(buf).strip()
    return secs

def find_section(secs, *needles):
    for k, v in secs.items():
        kl = k.lower()
        if all(n in kl for n in needles):
            return v
    return ""

def clean_inline(t):
    t = t.replace("**","")
    return t.strip()

def parse_script(path, posted_dir=None):
    date_str = os.path.splitext(os.path.basename(path))[0]
    try:
        d = datetime.date.fromisoformat(date_str)
    except ValueError:
        return None
    md = open(path, encoding="utf-8").read()
    secs = split_sections(md)
    posted_text = None
    if posted_dir:
        pp = os.path.join(posted_dir, date_str + ".md")
        if os.path.exists(pp):
            posted_text = open(pp, encoding="utf-8").read().strip()

    title = clean_inline(find_section(secs, "title")).split("\n")[0].strip()
    if not title:
        # fallback: first H1
        m = re.search(r"^#\s+(.*)", md, re.M)
        title = m.group(1).strip() if m else date_str

    caption = find_section(secs, "linkedin")
    teleprompter = find_section(secs, "teleprompter")

    # body paragraphs from caption (public voice), strip hashtag-only lines
    body_src = posted_text if posted_text else (caption if caption else teleprompter)
    paras = []
    for blk in re.split(r"\n\s*\n", body_src):
        blk = blk.strip()
        if not blk: continue
        if blk.startswith("#"): continue                      # hashtag line
        if set(blk) <= set("-\u2014\u2013*_ "): continue        # markdown rule / separator
        low = blk.lower()
        if "inbox is open" in low: continue                   # LinkedIn soft-close (not for articles)
        if low.startswith("if you're quietly weighing"): continue
        if low.startswith("if you're weighing"): continue
        if low.startswith("here's what's moving"): continue   # video-ism
        txt = scrub_signoff(" ".join(blk.split("\n")))
        if txt:
            paras.append(txt)

    # sources: clean, deduped PUBLICATION mastheads (no headlines, no author names, no "(Outlook)")
    PUBS = [("bloomberg law","Bloomberg Law"),("american lawyer","The American Lawyer"),
            ("national law journal","The National Law Journal"),("the recorder","The Recorder"),
            ("law360","Law360"),("reuters","Reuters"),("above the law","Above the Law"),
            ("corporate counsel","Corporate Counsel"),("law.com","Law.com"),("alm","ALM")]
    src_block = find_section(secs, "source")
    sources = []
    for line in src_block.splitlines():
        ss = line.strip()
        if re.match(r"^(NOT USED|CARRYOVER|ALSO AVAILABLE|No Law\.com|No Twitter)", ss, re.I):
            break
        if not re.match(r"^\d+\.", ss):
            continue
        low = ss.lower()
        for key, name in PUBS:
            if key in low and name not in sources:
                sources.append(name)
    # prefer specific ALM mastheads over generic Law.com / ALM when both present
    if any(p in sources for p in ("The American Lawyer","The National Law Journal","The Recorder")):
        sources = [p for p in sources if p not in ("Law.com","ALM")]

    # meta description: most substantive of the first few paragraphs (skip short openers)
    cand = [p for p in paras[:3] if len(p) > 60] or paras[:1] or [title]
    desc = re.sub(r"\s+", " ", max(cand, key=len))
    if len(desc) > 158:
        desc = desc[:155].rsplit(" ",1)[0] + "..."

    slug = slugify(title, d)
    return dict(date=d, date_str=date_str, title=title, paras=paras,
                sources=sources, desc=desc, slug=slug)

def slugify(title, d):
    base = re.sub(r"[^a-z0-9]+","-", title.lower()).strip("-")
    words = base.split("-")[:8]
    return f"{d.isoformat()}-" + "-".join(w for w in words if w)

def pretty_date(d):
    return f"{d.strftime('%A')}, {MONTHS[d.month-1]} {d.day}, {d.year}"

# ---------- templates ----------
HEAD_COMMON = """  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='17' fill='none' stroke='%23B9721E' stroke-width='1.5'/%3E%3Ccircle cx='20' cy='20' r='14' fill='none' stroke='%23B9721E' stroke-width='1'/%3E%3Ctext x='20' y='27' font-family='Georgia,serif' font-size='18' text-anchor='middle' fill='%23B9721E'%3EL%3C/text%3E%3C/svg%3E" />"""

NAV = """<header class="nav">
  <a class="brand" href="/#top" aria-label="Lionpoint Partners">
    <span class="brand-text">LIONPOINT</span>
  </a>
  <nav class="nav-links">
    <a href="/#practice">Services</a>
    <a href="/#approach">Approach</a>
    <a href="/#work">Placements</a>
    <a href="/market-pulse/" aria-current="page">Market Pulse</a>
    <a href="/#contact">Contact</a>
  </nav>
  <div class="nav-cta">
    <a class="btn btn-primary" href="/#contact"><span>Start a conversation</span></a>
  </div>
</header>"""

FOOT = """<footer class="foot pulse-foot">
  <div class="foot-bottom">
    <span>&copy; %YEAR% Lionpoint Partners LLC</span>
    <span>Confidentiality &middot; NALSC Code of Ethics &middot; Privacy</span>
    <span><a href="/market-pulse/feed.xml">RSS</a> &middot; New York City</span>
  </div>
</footer>""".replace("%YEAR%", str(datetime.date.today().year))

def article_html(a):
    canonical = f"{DOMAIN}/market-pulse/{a['slug']}.html"
    iso = a['date'].isoformat()
    body = "\n".join(f'      <p>{html.escape(p)}</p>' for p in a['paras'])
    if a['sources']:
        pubs = a['sources']
        if len(pubs) == 1:
            joined = pubs[0]
        elif len(pubs) == 2:
            joined = pubs[0] + " and " + pubs[1]
        else:
            joined = ", ".join(pubs[:-1]) + ", and " + pubs[-1]
        sources = ('    <div class="pulse-sources">\n      <h2>Sources</h2>\n'
                   f'      <p>Drawn from public reporting by {html.escape(joined)}.</p>\n    </div>')
    else:
        sources = ""
    ld = {
      "@context":"https://schema.org","@type":"NewsArticle",
      "headline": a['title'],
      "datePublished": iso, "dateModified": iso,
      "url": canonical, "mainEntityOfPage": canonical,
      "inLanguage":"en-US",
      "author":{"@type":"Organization","name":SITE,"url":DOMAIN},
      "publisher":{"@type":"Organization","name":SITE,"url":DOMAIN,
                   "logo":{"@type":"ImageObject","url":LOGO}},
      "description": a['desc'],
      "articleSection":"Market Pulse",
      "about":"US legal lateral partner market and BigLaw news"
    }
    crumb = {
      "@context":"https://schema.org","@type":"BreadcrumbList",
      "itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":DOMAIN+"/"},
        {"@type":"ListItem","position":2,"name":"Market Pulse","item":DOMAIN+"/market-pulse/"},
        {"@type":"ListItem","position":3,"name":a['title'],"item":canonical}
      ]}
    T = """<!doctype html>
<html lang="en">
<head>
  <title>%TITLE% | Market Pulse | Lionpoint Partners</title>
  <meta name="description" content="%DESC%" />
  <link rel="canonical" href="%CANON%" />
%HEAD%
  <link rel="stylesheet" href="/styles.css" />
  <link rel="stylesheet" href="/pulse.css" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Lionpoint Partners" />
  <meta property="og:title" content="%TITLE%" />
  <meta property="og:description" content="%DESC%" />
  <meta property="og:url" content="%CANON%" />
  <meta property="og:image" content="%OG%" />
  <meta property="article:published_time" content="%ISO%" />
  <meta property="article:section" content="Market Pulse" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="%TITLE%" />
  <meta name="twitter:description" content="%DESC%" />
  <meta name="twitter:image" content="%OG%" />
  <script type="application/ld+json">%LD%</script>
  <script type="application/ld+json">%CRUMB%</script>
</head>
<body class="pulse-page">
%NAV%
<main class="pulse-wrap">
  <article class="pulse-article">
    <nav class="pulse-breadcrumb" aria-label="Breadcrumb">
      <a href="/">Home</a> <span>/</span> <a href="/market-pulse/">Market Pulse</a>
    </nav>
    <div class="pulse-tag">Daily Market Pulse</div>
    <h1 class="pulse-h1">%TITLE%</h1>
    <time class="pulse-date" datetime="%ISO%">%PRETTY%</time>
    <div class="pulse-body">
%BODY%
    </div>
%SOURCES%
    <div class="pulse-cta">
      <p>Quietly weighing your next move, or building a practice?</p>
      <a class="btn btn-primary lg" href="mailto:aburak@lionpointpartners.com?subject=Confidential%20Introduction"><span>Start a confidential conversation</span></a>
    </div>
    <a class="pulse-back" href="/market-pulse/">&larr; All Market Pulse updates</a>
  </article>
</main>
%FOOT%
</body>
</html>"""
    return (T.replace("%HEAD%", HEAD_COMMON).replace("%NAV%", NAV).replace("%FOOT%", FOOT)
             .replace("%TITLE%", html.escape(a['title']))
             .replace("%DESC%", html.escape(a['desc']))
             .replace("%CANON%", canonical)
             .replace("%OG%", DOMAIN+"/market-pulse/og-default.png")
             .replace("%ISO%", iso).replace("%PRETTY%", pretty_date(a['date']))
             .replace("%BODY%", body).replace("%SOURCES%", sources)
             .replace("%LD%", json.dumps(ld)).replace("%CRUMB%", json.dumps(crumb)))

def hub_html(arts):
    cards = []
    for a in arts:
        cards.append(f'''      <a class="insight" href="/market-pulse/{a['slug']}.html">
        <span class="insight-tag">{pretty_date(a['date'])}</span>
        <h3>{html.escape(a['title'])}</h3>
        <span class="insight-read">Read the update</span>
      </a>''')
    grid = "\n".join(cards)
    canonical = DOMAIN + "/market-pulse/"
    desc = ("Market Pulse: Lionpoint Partners' daily read on the US legal lateral market. "
            "Partner moves, lateral hiring trends, and BigLaw business news for attorneys weighing their next move.")
    ld = {
      "@context":"https://schema.org","@type":"Blog",
      "name":"Market Pulse — Lionpoint Partners","url":canonical,
      "description":desc,"inLanguage":"en-US",
      "publisher":{"@type":"Organization","name":SITE,"url":DOMAIN,
                   "logo":{"@type":"ImageObject","url":LOGO}},
      "blogPost":[{"@type":"BlogPosting","headline":a['title'],
                   "datePublished":a['date'].isoformat(),
                   "url":f"{DOMAIN}/market-pulse/{a['slug']}.html"} for a in arts[:20]]
    }
    T = """<!doctype html>
<html lang="en">
<head>
  <title>Market Pulse | US Legal Lateral Market News | Lionpoint Partners</title>
  <meta name="description" content="%DESC%" />
  <link rel="canonical" href="%CANON%" />
%HEAD%
  <link rel="stylesheet" href="/styles.css" />
  <link rel="stylesheet" href="/pulse.css" />
  <link rel="alternate" type="application/rss+xml" title="Lionpoint Market Pulse" href="/market-pulse/feed.xml" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Lionpoint Partners" />
  <meta property="og:title" content="Market Pulse | Lionpoint Partners" />
  <meta property="og:description" content="%DESC%" />
  <meta property="og:url" content="%CANON%" />
  <meta property="og:image" content="%OG%" />
  <meta name="twitter:card" content="summary_large_image" />
  <script type="application/ld+json">%LD%</script>
</head>
<body class="pulse-page">
%NAV%
<main class="pulse-wrap">
  <header class="pulse-hero">
    <span class="eyebrow"><span class="eyebrow-num">&bull;</span> Market Pulse</span>
    <h1 class="section-title">The market, <em>read daily.</em></h1>
    <p class="section-lede">A fast, recruiter's-lens read on the US legal market: partner moves, lateral hiring trends, and the BigLaw business news that actually moves careers. Published most weekday mornings.</p>
  </header>
  <section class="insights-grid pulse-grid">
%GRID%
  </section>
</main>
%FOOT%
</body>
</html>"""
    return (T.replace("%HEAD%", HEAD_COMMON).replace("%NAV%", NAV).replace("%FOOT%", FOOT)
             .replace("%DESC%", html.escape(desc)).replace("%CANON%", canonical)
             .replace("%OG%", DOMAIN+"/market-pulse/og-default.png")
             .replace("%GRID%", grid).replace("%LD%", json.dumps(ld)))

def sitemap(arts):
    today = datetime.date.today().isoformat()
    urls = [(DOMAIN+"/", today, "1.0"),
            (DOMAIN+"/market-pulse/", today, "0.9")]
    for a in arts:
        urls.append((f"{DOMAIN}/market-pulse/{a['slug']}.html", a['date'].isoformat(), "0.7"))
    body = "\n".join(
      f'  <url><loc>{u}</loc><lastmod>{m}</lastmod><priority>{p}</priority></url>'
      for u,m,p in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + body + "\n</urlset>\n")

def rss(arts):
    items = []
    for a in arts[:25]:
        link = f"{DOMAIN}/market-pulse/{a['slug']}.html"
        pub = datetime.datetime.combine(a['date'], datetime.time(9,0)).strftime("%a, %d %b %Y %H:%M:%S +0000")
        items.append(f"""    <item>
      <title>{html.escape(a['title'])}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{pub}</pubDate>
      <description>{html.escape(a['desc'])}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Lionpoint Partners — Market Pulse</title>
  <link>{DOMAIN}/market-pulse/</link>
  <description>Daily read on the US legal lateral market.</description>
  <language>en-us</language>
{chr(10).join(items)}
</channel></rss>
"""

ROBOTS = f"""User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""

PULSE_CSS = """/* Market Pulse section - matches Lionpoint design system */
.pulse-page { background: var(--bg); color: var(--ink); }
.pulse-wrap { max-width: 860px; margin: 0 auto; padding: clamp(40px,7vw,110px) var(--pad) 80px; }
.pulse-page .nav { position: sticky; top: 0; background: rgba(244,238,226,.85); backdrop-filter: blur(8px); z-index: 50; }

/* hub hero */
.pulse-hero { max-width: var(--maxw); margin: 0 auto; padding-bottom: clamp(28px,4vw,52px); }
.pulse-hero .section-title { margin-top: 10px; }
.pulse-grid { max-width: var(--maxw); margin: 0 auto; }
.insight { text-decoration: none; color: var(--ink); }

/* article */
.pulse-breadcrumb { font-family: var(--font-mono); font-size: 12px; letter-spacing:.06em; color: var(--ink-mute); margin-bottom: 28px; }
.pulse-breadcrumb a { color: var(--ink-dim); text-decoration: none; }
.pulse-breadcrumb a:hover { color: var(--accent); }
.pulse-breadcrumb span { margin: 0 8px; color: var(--line-2); }
.pulse-tag { font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing:.16em; color: var(--accent); margin-bottom: 18px; }
.pulse-h1 { font-family: var(--font-display); font-weight: 400; font-size: clamp(32px,5vw,58px); line-height: 1.02; letter-spacing: -0.03em; margin: 0 0 18px; }
.pulse-date { display:block; font-family: var(--font-mono); font-size: 12px; letter-spacing:.08em; color: var(--ink-mute); margin-bottom: 40px; }
.pulse-body p { font-family: var(--font-sans); font-size: 18px; line-height: 1.72; color: var(--ink-dim); margin: 0 0 22px; }
.pulse-body p:first-child { font-size: 20px; color: var(--ink); }

.pulse-sources { margin: 48px 0 0; padding-top: 28px; border-top: 1px solid var(--line); }
.pulse-sources h2 { font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing:.14em; color: var(--ink-mute); font-weight: 500; margin: 0 0 16px; }
.pulse-sources ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.pulse-sources li { font-size: 14px; line-height: 1.5; color: var(--ink-dim); padding-left: 18px; position: relative; }
.pulse-sources li::before { content: "/"; position: absolute; left: 0; color: var(--accent); font-family: var(--font-mono); }
.pulse-sources a { color: var(--ink); text-decoration: none; border-bottom: 1px solid var(--line-2); }
.pulse-sources a:hover { color: var(--accent); border-color: var(--accent); }

.pulse-cta { margin: 56px 0 40px; padding: clamp(28px,4vw,44px); border: 1px solid var(--line); border-radius: 16px; background: var(--bg-3); text-align: center; }
.pulse-cta p { font-family: var(--font-display); font-size: clamp(20px,2.4vw,26px); margin: 0 0 22px; color: var(--ink); }
.pulse-back { display: inline-block; font-family: var(--font-mono); font-size: 13px; letter-spacing:.05em; color: var(--ink-dim); text-decoration: none; }
.pulse-back:hover { color: var(--accent); }
.pulse-foot { border-top: 1px solid var(--line); margin-top: 40px; }
.pulse-foot .foot-bottom { max-width: var(--maxw); margin: 0 auto; padding: 28px var(--pad); display:flex; flex-wrap:wrap; gap: 14px 28px; justify-content: space-between; font-family: var(--font-mono); font-size: 12px; color: var(--ink-mute); }
.pulse-foot a { color: var(--ink-dim); text-decoration: none; }
.pulse-foot a:hover { color: var(--accent); }
@media (max-width: 600px){ .pulse-foot .foot-bottom{ justify-content:flex-start; } }
"""

def patch_homepage(repo, link_nav=False):
    p = os.path.join(repo, "index.html")
    h = open(p, encoding="utf-8").read()
    # 1) nav link (only in linked mode)
    if link_nav and "/market-pulse/" not in h:
        h = h.replace('    <a href="#work">Placements</a>\n',
                      '    <a href="#work">Placements</a>\n    <a href="/market-pulse/">Market Pulse</a>\n', 1)
        # footer Firm column
        h = h.replace('        <a href="#contact">Contact</a>\n      </div>\n      <div>\n        <h4>Office</h4>',
                      '        <a href="#contact">Contact</a>\n        <a href="/market-pulse/">Market Pulse</a>\n      </div>\n      <div>\n        <h4>Office</h4>', 1)
    # 2) SEO head block (idempotent)
    if "og:site_name" not in h:
        org = {
          "@context":"https://schema.org","@type":["Organization","ProfessionalService"],
          "name":SITE,"url":DOMAIN+"/","logo":LOGO,
          "description":"New York based, NALSC member legal search firm representing attorneys on lateral, group, and in-house moves with top-tier US law firms.",
          "areaServed":"US","knowsAbout":["Legal recruiting","Lateral partner moves","BigLaw hiring","Associate placement"],
          "address":{"@type":"PostalAddress","streetAddress":"199 Water Street","addressLocality":"New York","addressRegion":"NY","addressCountry":"US"},
          "email":"aburak@lionpointpartners.com",
          "memberOf":{"@type":"Organization","name":"National Association of Legal Search Consultants"}
        }
        site_ld = {"@context":"https://schema.org","@type":"WebSite","name":SITE,"url":DOMAIN+"/"}
        seo = f"""<link rel="canonical" href="{DOMAIN}/" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Lionpoint Partners" />
<meta property="og:title" content="Lionpoint Partners | Legal Search Firm" />
<meta property="og:description" content="New York based, NALSC member legal search firm. We represent attorneys making lateral, group, and in-house moves with top-tier law firms." />
<meta property="og:url" content="{DOMAIN}/" />
<meta property="og:image" content="{DOMAIN}/og-default.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Lionpoint Partners | Legal Search Firm" />
<meta name="twitter:description" content="New York based, NALSC member legal search firm representing attorneys on lateral, group, and in-house moves." />
<meta name="twitter:image" content="{DOMAIN}/og-default.png" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="author" content="Lionpoint Partners" />
<link rel="alternate" type="application/rss+xml" title="Lionpoint Market Pulse" href="/market-pulse/feed.xml" />
<script type="application/ld+json">{json.dumps(org)}</script>
<script type="application/ld+json">{json.dumps(site_ld)}</script>
</head>"""
        h = h.replace("</head>", seo, 1)
    open(p, "w", encoding="utf-8").write(h)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scripts", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--link-nav", action="store_true", help="add Market Pulse nav/footer links (off = soft launch)")
    ap.add_argument("--posted", default=None, help="dir of posted LinkedIn captions YYYY-MM-DD.md; overrides script caption when present")
    args = ap.parse_args()
    arts = []
    for f in sorted(glob.glob(os.path.join(args.scripts, "*.md"))):
        a = parse_script(f, args.posted)
        if a and a['paras']:
            arts.append(a)
    arts.sort(key=lambda a: a['date'], reverse=True)

    mp = os.path.join(args.repo, "market-pulse")
    os.makedirs(mp, exist_ok=True)
    for a in arts:
        open(os.path.join(mp, a['slug']+".html"), "w", encoding="utf-8").write(article_html(a))
    open(os.path.join(mp, "index.html"), "w", encoding="utf-8").write(hub_html(arts))
    open(os.path.join(mp, "feed.xml"), "w", encoding="utf-8").write(rss(arts))
    open(os.path.join(args.repo, "sitemap.xml"), "w", encoding="utf-8").write(sitemap(arts))
    open(os.path.join(args.repo, "robots.txt"), "w", encoding="utf-8").write(ROBOTS)
    open(os.path.join(args.repo, "pulse.css"), "w", encoding="utf-8").write(PULSE_CSS)
    patch_homepage(args.repo, args.link_nav)
    print(f"Generated {len(arts)} articles + hub + sitemap + rss + robots + pulse.css")
    print("Latest:", arts[0]['slug'] if arts else "(none)")

if __name__ == "__main__":
    main()
