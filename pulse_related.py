#!/usr/bin/env python3
"""Market Pulse -> practice/market internal links ("Related recruiting" block).

Why: Market Pulse articles are the pages Google already ranks well (avg position ~5-10,
most of the site's non-brand clicks). The practice/market pages it should rank for
commercial queries got no links from them. This adds 2-5 contextual links per article,
chosen from what the article actually covers (practice + city mentioned in the same
sentence -> practice-in-city page; otherwise the city hub and practice hub).

Idempotent post-processor: rewrites the block between markers on every run, so
build_pulse.py can call it after (re)generating articles and it can be run alone.
Only links to pages that exist in the repo.

Usage: python3 pulse_related.py --repo <dir>
"""
import os, re, glob, html, argparse

START = "<!-- related:start -->"
END = "<!-- related:end -->"

# Practice slug -> (display name, regex patterns matched on lowercased sentence text)
PRACTICE_KW = [
 ("ip-litigation", "IP litigation", [r"patent litigat", r"\bip litigat", r"\bitc\b", r"\bptab\b", r"patent (?:trial|case|dispute)"]),
 ("real-estate-litigation", "Real estate litigation", [r"real estate litigat", r"real estate dispute"]),
 ("private-investment-funds", "Private investment funds", [r"fund formation", r"private funds?\b", r"investment funds?\b", r"investment management", r"asset management", r"secondaries"]),
 ("private-equity", "Private equity", [r"private equity", r"\bbuyouts?\b", r"\bsponsors?\b"]),
 ("emerging-companies-venture-capital", "Emerging companies and venture capital", [r"venture[- ](?:capital|backed|fund|financ|investor|deal|lawyer|practice)", r"\bvc\b", r"emerging compan", r"\bstartups?\b", r"\becvc\b"]),
 ("capital-markets", "Capital markets", [r"capital markets", r"\bipos?\b", r"high[- ]yield", r"securities offering"]),
 ("banking-finance", "Banking and finance", [r"\b(?:debt|leveraged|acquisition|project|structured|fund) finance", r"private credit", r"\blending\b", r"\bbanking\b", r"\bfinance partner"]),
 ("mergers-acquisitions", "Mergers and acquisitions", [r"\bm&a\b", r"\bm&amp;a\b", r"mergers? and acquisitions", r"\bdealmakers?\b"]),
 ("real-estate", "Real estate", [r"real estate(?! litigat)(?! dispute)"]),
 ("antitrust", "Antitrust", [r"antitrust", r"competition law", r"merger review"]),
 ("restructuring-bankruptcy", "Restructuring and bankruptcy", [r"restructuring", r"bankruptcy", r"\bdistressed\b", r"insolvency", r"chapter 11"]),
 ("regulatory", "Regulatory", [r"regulatory", r"white[- ]collar", r"\benforcement\b", r"investigations?\b", r"\bcompliance\b"]),
 ("labor-employment", "Labor and employment", [r"\bemployment\b", r"\blabor\b", r"wage[- ]and[- ]hour", r"\bworkplace\b"]),
 ("intellectual-property", "Intellectual property", [r"intellectual property", r"\bpatents?\b", r"trademark", r"\blicensing\b"]),
 ("commercial-litigation", "Commercial litigation", [r"litigat", r"\btrial\b", r"\bdisputes?\b", r"\barbitration\b"]),
]
CITY_KW = [
 ("new-york", "New York", [r"new york", r"\bnyc\b", r"manhattan"]),
 ("washington-dc", "Washington, DC", [r"\bwashington\b(?!,? state)", r"\bd\.?c\.?\b"]),
 ("boston", "Boston", [r"\bboston\b"]),
 ("los-angeles", "Los Angeles", [r"los angeles", r"century city"]),
 ("philadelphia", "Philadelphia", [r"philadelphia"]),
 ("chicago", "Chicago", [r"chicago"]),
 ("atlanta", "Atlanta", [r"atlanta"]),
 ("san-francisco", "San Francisco", [r"san francisco", r"bay area", r"silicon valley", r"palo alto"]),
 ("denver", "Denver", [r"\bdenver\b"]),
 ("miami", "Miami", [r"\bmiami\b"]),
 ("san-diego", "San Diego", [r"san diego"]),
 ("dallas", "Dallas", [r"\bdallas\b"]),
 ("houston", "Houston", [r"\bhouston\b"]),
 ("austin", "Austin", [r"\baustin\b"]),
 ("charlotte", "Charlotte", [r"\bcharlotte\b"]),
]
MAX_LINKS = 5
NOT_PLACES = {"sidley austin": "sidley", "sidley, austin": "sidley", "boston consulting": "bcg",
              "boston scientific": "bsci", "washington post": "wapo", "jackson walker": "jw",
              "charlotte's": "charlottes"}

# when a specific practice matched, drop the generic one it implies
SUPERSEDES = {"ip-litigation": ["commercial-litigation", "intellectual-property"],
              "real-estate-litigation": ["commercial-litigation"]}

def _hits(text, table):
    out = []
    for slug, name, pats in table:
        if any(re.search(p, text) for p in pats):
            out.append((slug, name))
    drop = {d for slug, _ in out for d in SUPERSEDES.get(slug, [])}
    return [(s, n) for s, n in out if s not in drop]

_VERB = r"(?:added|adds|brought|brings|poached|hired|hires|took|takes|pulled|recruited|picked|landed|lured|tapped|grabbed|nabbed|named|launched|opened|lost|loses)"
_CLAUSE = re.compile(r";|: |, while |,? and (?=(?:\S+ ){0,6}" + _VERB + r"\b)|, (?=(?:\S+ ){0,6}" + _VERB + r"\b)")

def _sentences(text):
    """Sentences, further split into one clause per move so a practice and a city are only
    paired when they describe the same hire (run-on 'lateral wire' sentences list several)."""
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", text):
        out += [c for c in _CLAUSE.split(sent) if c and c.strip()]
    return out

def pick_links(body_text, exists):
    """Return [(anchor, url)] for an article body. exists(url) -> bool."""
    text = html.unescape(body_text).lower()
    # firm and company names that contain a city name are not location mentions
    for name in NOT_PLACES:
        text = text.replace(name, NOT_PLACES[name])
    links, seen = [], set()
    def add(anchor, url):
        if url in seen or not exists(url) or len(links) >= MAX_LINKS:
            return
        seen.add(url); links.append((anchor, url))
    # 1) practice + city in the same sentence -> combo page (most specific, most accurate)
    for s in _sentences(text):
        cities = _hits(s, CITY_KW)
        pracs = _hits(s, PRACTICE_KW)
        for cslug, cname in cities:
            for pslug, pname in pracs[:2]:
                add(f"{pname} legal recruiters in {cname}", f"/practices/{pslug}/{cslug}/")
    # 2) city hubs for cities the article covers
    for cslug, cname in _hits(text, CITY_KW):
        add(f"Legal recruiters in {cname}", f"/markets/{cslug}/")
    # 3) practice hubs
    for pslug, pname in _hits(text, PRACTICE_KW):
        add(f"{pname} legal recruiters", f"/practices/{pslug}/")
    return links

def block_html(links):
    if not links:
        return f"{START}{END}"
    items = "\n".join(f'        <li><a href="{u}">{html.escape(a)}</a></li>' for a, u in links)
    return (f"{START}\n    <nav class=\"pulse-related\" aria-label=\"Related recruiting coverage\">\n"
            f"      <h2>Related recruiting coverage</h2>\n      <ul>\n{items}\n      </ul>\n"
            f"      <p class=\"pulse-related-more\">Browse all <a href=\"/practices/\">practices</a> and <a href=\"/markets/\">markets</a>.</p>\n"
            f"    </nav>\n    {END}")

def apply(repo):
    def exists(url):
        return os.path.exists(os.path.join(repo, url.strip("/"), "index.html"))
    n = changed = 0
    for f in sorted(glob.glob(os.path.join(repo, "market-pulse", "2*.html"))):
        h = open(f, encoding="utf-8").read()
        m = re.search(r'<div class="pulse-body">(.*?)</div>', h, re.S)
        if not m:
            continue
        body = re.sub(r"<[^>]+>", " ", m.group(1))
        blk = block_html(pick_links(body, exists))
        if START in h:
            new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: blk, h, flags=re.S)
        else:
            anchor = '    <div class="pulse-cta">'
            if anchor not in h:
                continue
            new = h.replace(anchor, "    " + blk + "\n" + anchor, 1)
        n += 1
        if new != h:
            open(f, "w", encoding="utf-8").write(new); changed += 1
    # hub page: one-line pointer to the practice and market pages
    hub = os.path.join(repo, "market-pulse", "index.html")
    if os.path.exists(hub):
        h = open(hub, encoding="utf-8").read()
        line = (f'{START}<p class="pulse-related-more" style="margin-top:14px">Recruiting coverage: '
                f'<a href="/practices/">by practice</a> &middot; <a href="/markets/">by market</a> &middot; '
                f'<a href="/associates/">associates</a></p>{END}')
        if START in h:
            new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: line, h, flags=re.S)
        else:
            new = h.replace("</p>\n  </header>", "</p>\n    " + line + "\n  </header>", 1)
        if new != h:
            open(hub, "w", encoding="utf-8").write(new)
    return n, changed

RELATED_CSS = """
/* related recruiting links (pulse_related.py) */
.pulse-related { margin: 44px 0 0; padding-top: 26px; border-top: 1px solid var(--line); }
.pulse-related h2 { font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing:.14em; color: var(--ink-mute); font-weight: 500; margin: 0 0 14px; }
.pulse-related ul { list-style: none; padding: 0; margin: 0 0 14px; display: grid; gap: 8px; }
.pulse-related li { font-size: 15px; line-height: 1.5; padding-left: 18px; position: relative; }
.pulse-related li::before { content: "/"; position: absolute; left: 0; color: var(--accent); font-family: var(--font-mono); }
.pulse-related a { color: var(--ink); text-decoration: none; border-bottom: 1px solid var(--line-2); }
.pulse-related a:hover { color: var(--accent); border-color: var(--accent); }
.pulse-related-more { font-size: 14px; color: var(--ink-mute); margin: 0; }
"""

def ensure_css(repo):
    p = os.path.join(repo, "pulse.css")
    if not os.path.exists(p):
        return
    css = open(p, encoding="utf-8").read()
    if ".pulse-related" not in css:
        open(p, "a", encoding="utf-8").write(RELATED_CSS)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True)
    a = ap.parse_args()
    ensure_css(a.repo)
    n, c = apply(a.repo)
    print(f"pulse_related: {n} articles scanned, {c} updated")
