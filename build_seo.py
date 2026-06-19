#!/usr/bin/env python3
"""Lionpoint SEO matrix generator with auto 'Recent moves' from Market Pulse + drip release.
Usage: python3 build_seo.py --repo <dir> [--advance N]
- Generates practice / city / practice-in-city pages, each with a live 'Recent moves'
  section linking relevant Market Pulse articles (parsed from <repo>/market-pulse/).
- Drip release: a manifest (seo-release.json) tracks how many pages are live; --advance N
  releases N more this run. Already-live pages are regenerated so Recent moves stay fresh.
- Writes sitemap-seo.xml of released pages.
"""
import os, re, html, json, glob, argparse, datetime
DOMAIN="https://lionpointpartners.com"; M="aburak@lionpointpartners.com"

PRACTICES=[
 ("mergers-acquisitions","Mergers & Acquisitions","M&A",["Lateral M&A partners with a portable transactional book","Multi-partner corporate and M&A teams","Practice build-outs for firms entering or scaling M&A","Partners spanning public company, private deals, and joint ventures"],"M&A is the engine of most corporate practices, and firms compete hardest for dealmakers who bring institutional and sponsor relationships.",["m&a","merger","acquisition"]),
 ("private-equity","Private Equity","private equity",["Sponsor-side PE partners with portable fund relationships","Buyout, growth, and secondaries-focused dealmakers","Fund-to-firm and lateral partner moves","Teams building a dedicated private equity bench"],"Private equity has been one of the most aggressively recruited practices, with firms paying up for partners who own the sponsor relationship.",["private equity","buyout"]),
 ("capital-markets","Capital Markets","capital markets",["Equity and debt capital markets partners","Securities and public company advisory partners","IPO and high-yield focused practitioners","Teams supporting a capital markets build-out"],"Capital markets hiring tracks the deal pipeline, and demand rises sharply when the IPO and high-yield windows open.",["capital markets","ipo","securities","high-yield"]),
 ("banking-finance","Banking & Finance","banking and finance",["Leveraged and acquisition finance partners","Direct lending and private credit practitioners","Restructuring-adjacent special situations finance","Lender and borrower-side finance teams"],"Banking and finance has been a top growth target as private credit reshapes how deals are funded.",["finance","lending","private credit","leveraged"]),
 ("private-investment-funds","Private Investment Funds","private funds",["Fund formation partners with sponsor relationships","Private equity, credit, and real estate fund practitioners","Secondaries and co-investment focused partners","Teams building a private funds practice"],"Fund formation is a relationship-driven practice where a portable sponsor base is the whole game.",["fund formation","private funds","investment funds","secondaries"]),
 ("real-estate","Real Estate","real estate",["Real estate partners with a portable transactional book","Acquisitions, development, and JV practitioners","Real estate finance and funds partners","Teams and office build-outs in real estate"],"Real estate spans acquisitions, development, finance, funds, and joint ventures, and firms compete hardest for partners with durable client relationships.",["real estate"]),
 ("emerging-companies-venture-capital","Emerging Companies & Venture Capital","ECVC",["ECVC partners with a portable company and fund base","Startup, growth, and venture financing practitioners","Partners bridging company-side and investor-side work","Teams building a venture and emerging companies practice"],"Emerging companies and venture capital is a network practice, and the partners with the founder and fund relationships have real leverage.",["venture","emerging companies","ecvc","vc"]),
 ("commercial-litigation","Commercial Litigation","commercial litigation",["Commercial and business litigation partners","Complex disputes and trial practitioners","Partners with a portable client and matter base","Teams expanding a litigation bench"],"Litigation hiring rewards partners who control client relationships and can carry a book of matters between platforms.",["litigation","disputes"]),
 ("real-estate-litigation","Real Estate Litigation","real estate litigation",["Real estate and property disputes partners","Land use, development, and lease litigation practitioners","Partners bridging transactional and disputes work","Teams adding a real estate litigation capability"],"Real estate litigation sits at the intersection of property, development, and finance disputes, and pairs naturally with a transactional bench.",["real estate","litigation"]),
 ("ip-litigation","IP Litigation","IP litigation",["Patent and IP litigation partners","Trial-ready practitioners with a portable docket","ITC, district court, and PTAB focused partners","Teams building an IP litigation practice"],"IP litigation is docket-driven, and partners who bring portable matters and client relationships are the ones firms chase.",["patent","ip litigation","intellectual property"]),
 ("antitrust","Antitrust","antitrust",["Antitrust and competition partners","Merger review and government investigations practitioners","Civil litigation and counseling focused partners","Teams expanding an antitrust capability"],"Antitrust demand moves with the enforcement climate, and firms value partners with agency credibility and a portable practice.",["antitrust","competition"]),
 ("intellectual-property","Intellectual Property","intellectual property",["Patent prosecution and IP transactional partners","Licensing, diligence, and portfolio practitioners","Partners with a portable client base","Teams building an IP transactional practice"],"Intellectual property work is relationship and portfolio driven, especially where it supports a strong life sciences or technology client base.",["intellectual property","patent","licensing"]),
 ("restructuring-bankruptcy","Restructuring & Bankruptcy","restructuring",["Restructuring and bankruptcy partners","Debtor, creditor, and special situations practitioners","Partners with a portable referral and client network","Teams building a restructuring bench"],"Restructuring is counter-cyclical, and firms staff up on partners with deep referral networks ahead of and through distressed cycles.",["restructuring","bankruptcy","distressed"]),
 ("regulatory","Regulatory","regulatory",["Regulatory and government enforcement partners","Financial services, healthcare, and energy regulatory practitioners","Investigations and compliance focused partners","Teams adding a regulatory capability"],"Regulatory hiring follows the agencies, and partners with sector credibility and a portable book are in steady demand.",["regulatory","compliance","enforcement"]),
 ("labor-employment","Labor & Employment","labor and employment",["Labor and employment partners","Wage-and-hour, litigation, and counseling practitioners","Partners with a portable client base","Teams building a labor and employment practice"],"Labor and employment is a volume and relationship practice where a portable client roster travels well between firms.",["employment","labor","wage and hour"]),
]
CITIES=[
 ("new-york","New York","the deepest legal market in the country, with leading benches across corporate, finance, funds, real estate, and litigation",["mergers-acquisitions","private-equity","capital-markets","banking-finance","private-investment-funds"],["new york"]),
 ("washington-dc","Washington, DC","the center of regulatory, antitrust, and government enforcement work",["regulatory","antitrust","commercial-litigation"],["washington","dc"]),
 ("boston","Boston","a hub for private equity, life sciences, intellectual property, and venture work",["private-equity","intellectual-property","emerging-companies-venture-capital","private-investment-funds"],["boston"]),
 ("los-angeles","Los Angeles","a market driven by entertainment, private equity, real estate, and disputes",["private-equity","real-estate","commercial-litigation"],["los angeles"," la "]),
 ("philadelphia","Philadelphia","a market anchored by litigation, life sciences, and healthcare work",["commercial-litigation","intellectual-property","labor-employment"],["philadelphia"]),
 ("chicago","Chicago","a center for restructuring, finance, and complex litigation",["restructuring-bankruptcy","banking-finance","commercial-litigation","mergers-acquisitions"],["chicago"]),
 ("atlanta","Atlanta","a fast-growing market for finance, real estate, and corporate work",["banking-finance","real-estate","mergers-acquisitions"],["atlanta"]),
 ("san-francisco","San Francisco","the heart of technology, venture, capital markets, and IP work",["emerging-companies-venture-capital","capital-markets","intellectual-property","private-equity"],["san francisco","bay area"]),
 ("denver","Denver","a growing market for venture, energy, and real estate work",["emerging-companies-venture-capital","real-estate","banking-finance"],["denver"]),
 ("miami","Miami","a rising market for funds, private equity, real estate, and Latin America-connected work",["private-investment-funds","private-equity","real-estate"],["miami"]),
 ("san-diego","San Diego","a center for intellectual property, life sciences, and patent work",["intellectual-property","ip-litigation","emerging-companies-venture-capital"],["san diego"]),
 ("dallas","Dallas","a market driven by energy, private equity, and M&A",["mergers-acquisitions","private-equity","real-estate"],["dallas"]),
 ("houston","Houston","the energy capital, with deep transactional, finance, and restructuring benches",["mergers-acquisitions","banking-finance","real-estate","restructuring-bankruptcy"],["houston"]),
 ("austin","Austin","a tech and venture hub with growing corporate and IP work",["emerging-companies-venture-capital","intellectual-property","mergers-acquisitions"],["austin"]),
 ("charlotte","Charlotte","a banking and structured finance center",["banking-finance","real-estate","capital-markets"],["charlotte"]),
]
PRAC={p[0]:p for p in PRACTICES}; CITY={c[0]:c for c in CITIES}

def parse_pulse(repo):
    arts=[]
    for f in glob.glob(os.path.join(repo,"market-pulse","2026-*.html")):
        h=open(f,encoding="utf-8").read()
        d=os.path.basename(f)[:10]
        t=re.search(r'<h1 class="pulse-h1">(.*?)</h1>',h,re.S)
        b=re.search(r'<div class="pulse-body">(.*?)</div>',h,re.S)
        if not (t and b): continue
        text=html.unescape(re.sub("<[^>]+>"," ",b.group(1))).lower()
        arts.append({"date":d,"title":html.unescape(re.sub("<[^>]+>","",t.group(1))),
                     "url":"/market-pulse/"+os.path.basename(f),"text":text})
    arts.sort(key=lambda a:a["date"],reverse=True)
    return arts

def recent_moves(arts, prac_kw=None, city_kw=None, n=3):
    out=[]
    for a in arts:
        ok=True
        if prac_kw is not None: ok = ok and any(k in a["text"] for k in prac_kw)
        if city_kw is not None: ok = ok and any(k in a["text"] for k in city_kw)
        if ok: out.append(a)
        if len(out)>=n: break
    if city_kw is not None and len(out)<n and prac_kw is not None:  # fallback to practice-only
        for a in arts:
            if a not in out and any(k in a["text"] for k in prac_kw):
                out.append(a)
            if len(out)>=n: break
    return out[:n]
print("data loaded:",len(PRACTICES),"practices",len(CITIES),"cities")

# ---------------- TEMPLATES ----------------
FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
def esc(s): return html.escape(s)
def nav():
    return ('<header class="nav"><a class="brand" href="/#top"><span class="brand-text">LIONPOINT</span></a>'
            '<nav class="nav-links"><a href="/#practice">Services</a><a href="/practices/">Practices</a>'
            '<a href="/#work">Placements</a><a href="/#contact">Contact</a></nav>'
            '<div class="nav-cta"><a class="btn btn-primary" href="/#contact"><span>Start a conversation</span></a></div></header>')
def foot():
    return ('<footer class="foot pmx-foot"><div class="foot-bottom"><span>&copy; 2026 Lionpoint Partners LLC</span>'
            '<span><a href="/practices/">Practices</a> &middot; <a href="/market-pulse/">Market Pulse</a></span><span>New York City</span></div></footer>')
def ctas(subj):
    return (f'<div class="hero-ctas" style="margin-top:6px"><a class="btn btn-primary lg" href="mailto:{M}?subject={subj}%20Introduction"><span>Confidential introduction</span></a>'
            f'<a class="btn btn-ghost lg" href="mailto:{M}?subject={subj}%20Search%20Inquiry"><span>Retain a search</span></a></div>')
def services(items):
    return '<div class="grid services">'+"".join(f'<article class="service"><div class="service-num">&rarr; 0{i+1}</div><h3>{esc(t.split(" with ")[0][:38])}</h3><p>{esc(t)}</p></article>' for i,t in enumerate(items))+'</div>'
def process():
    return ('<div class="process-grid">'
      '<article class="process-step"><div class="process-num">01</div><h3>Confidential Intro</h3><p>We talk. You tell us what you want in your next platform, and what you do not. We listen.</p></article>'
      '<article class="process-step"><div class="process-num">02</div><h3>Market Check</h3><p>We bring you a curated list of firms. You approve every one before we reach out on your behalf.</p></article>'
      '<article class="process-step"><div class="process-num">03</div><h3>Execution</h3><p>We handle scheduling, prep, and negotiation to maximize your platform and total package.</p></article></div>')
def faq_block(faqs):
    items="".join(f'<div class="faq-item"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q,a in faqs)
    ld={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]}
    return f'<div class="faq">{items}</div><script type="application/ld+json">{json.dumps(ld)}</script>'
def related(title,links):
    return f'<div class="rel-wrap"><div class="rel-eyebrow">{esc(title)}</div><div class="rel-grid">'+"".join(f'<a class="rel" href="{u}">{esc(t)}</a>' for t,u in links)+'</div></div>'
def recent_section(arts):
    if not arts: return ""
    cells="".join(f'<a class="rel" href="{a["url"]}"><span class="rel-date">{a["date"]}</span>{esc(a["title"])}</a>' for a in arts)
    return ('<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">RM</span> Recent moves</span>'
            f'<h2 class="section-title">From the <em>Market Pulse.</em></h2></div><div class="rel-wrap"><div class="rel-grid">{cells}</div></div></section>')
def cta_section():
    return ('<section class="section cta"><div class="cta-inner"><div class="cta-left"><span class="eyebrow"><span class="eyebrow-num">&rarr;</span> Start here</span>'
      '<h2 class="section-title">A confidential<br/>conversation.</h2><p class="section-lede">Whether you are quietly considering your next move or building a practice, a thirty-minute call costs nothing and usually clarifies a lot.</p></div>'
      f'<div class="cta-right"><a class="cta-box" href="mailto:{M}?subject=Confidential%20Introduction"><span class="cta-kicker">For Attorneys</span><span class="cta-head">Confidential introduction &rarr;</span></a>'
      f'<a class="cta-box" href="mailto:{M}?subject=Retained%20Search%20Inquiry"><span class="cta-kicker">For Law Firms</span><span class="cta-head">Retain a search &rarr;</span></a></div></div></section>')
def page(title,desc,canonical,crumbs,body):
    cl={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":DOMAIN+u} for i,(n,u) in enumerate(crumbs)]}
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
      f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}">{FONTS}'
      '<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/practices.css">'
      f'<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{DOMAIN}/og-default.png"><meta name="twitter:card" content="summary_large_image">'
      f'<script type="application/ld+json">{json.dumps(cl)}</script></head><body class="pmx-page">{nav()}<main class="pmx-wrap">{body}{cta_section()}</main>{foot()}</body></html>')

def _ipath(url): return url.strip("/")+"/index.html"
def live(links, rel): return [(t,u) for t,u in links if _ipath(u) in rel]
def related_section(num, eyebrow, title, links):
    if not links: return ""
    return (f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">{num}</span> {eyebrow}</span>'
            f'<h2 class="section-title">{title}</h2></div>{related(eyebrow,links)}</section>')
def page_order():
    o=["practices/index.html","markets/index.html"]
    o+=[f"practices/{p[0]}/index.html" for p in PRACTICES]
    o+=[f"markets/{c[0]}/index.html" for c in CITIES]
    o+=[f"practices/{p[0]}/{c[0]}/index.html" for c in CITIES for p in PRACTICES]
    return o

def build_all(repo, rel):
    arts=parse_pulse(repo); pages=[]
    pl=live([(p[1]+" Partner Recruiting",f"/practices/{p[0]}/") for p in PRACTICES], rel)
    pages.append(("practices/index.html", page("Legal Practice Recruiting | Lionpoint Partners",
        "Confidential partner and group recruiting across M&A, private equity, real estate, litigation, finance, IP, and more, for AmLaw 200 firms nationwide.",
        DOMAIN+"/practices/",[("Home","/"),("Practices","/practices/")],
        f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">00</span> Practices</span><h2 class="section-title">Recruiting by <em>practice.</em></h2><p class="section-lede">We run confidential partner and group searches across the practices below, nationwide and in your market. You can also browse <a href="/markets/">recruiting by city</a>.</p></div><section style="padding-top:0">{related("All practices",pl)}</section></section>')))
    cl=live([("Legal Recruiting in "+c[1],f"/markets/{c[0]}/") for c in CITIES], rel)
    pages.append(("markets/index.html", page("Legal Recruiters by Market | Lionpoint Partners",
        "Confidential partner and group recruiting in New York, DC, Boston, LA, Chicago, San Francisco, Houston, Miami, and more.",
        DOMAIN+"/markets/",[("Home","/"),("Markets","/markets/")],
        f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">00</span> Markets</span><h2 class="section-title">Recruiting by <em>market.</em></h2><p class="section-lede">We work nationally. Explore the markets where we run partner and group searches, or browse <a href="/practices/">recruiting by practice</a>.</p></div><section style="padding-top:0">{related("All markets",cl)}</section></section>')))
    for slug,name,kw,items,mkt,pkw in PRACTICES:
        rm=recent_section(recent_moves(arts,pkw))
        city_links=live([(f"{name} in {c[1]}",f"/practices/{slug}/{c[0]}/") for c in CITIES], rel)
        faqs=[(f"Do you handle confidential {kw} partner moves?","Yes. Every search is confidential and nothing goes out without your approval."),
              ("How do I know if my practice is portable enough to move?","Portability matters more than any single number. We give you an honest read on how your book and relationships are likely to be valued."),
              ("Do you represent firms or candidates?","Both. We run retained searches for firms and represent individual partners and groups exploring a move.")]
        body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">RE</span> Practice Focus</span><h1 class="section-title">{esc(name)} partner <em>recruiting.</em></h1>'
          f'<p class="section-lede">We represent {esc(kw)} partners and practice groups on confidential lateral moves to AmLaw 200 firms and leading boutiques across the United States. Every search is led by a recruiter who knows the {esc(kw)} market and the firms hiring in it.</p></div>{ctas(name.replace(" ","%20").replace("&","and"))}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">01</span> What we handle</span><h2 class="section-title">Searches across <em>{esc(kw)}.</em></h2></div>{services(items)}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">02</span> The market</span><h2 class="section-title">Where the market is <em>moving.</em></h2><p class="section-lede">{esc(mkt)}</p></div></section>'
          f'{rm}'
          f'<section class="section approach" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">03</span> The Process</span><h2 class="section-title">Three steps, <em>handled end to end.</em></h2></div>{process()}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">04</span> Questions</span><h2 class="section-title">{esc(name)} moves, <em>answered.</em></h2></div>{faq_block(faqs)}</section>'
          f'{related_section("05","Where we recruit",esc(name)+" by <em>city.</em>",city_links)}')
        pages.append((f"practices/{slug}/index.html", page(f"{name} Partner Recruiting | Lionpoint Partners",
            f"Lionpoint Partners recruits {kw} partners and groups for AmLaw 200 firms and boutiques nationwide. Confidential lateral search.",
            DOMAIN+f"/practices/{slug}/",[("Home","/"),("Practices","/practices/"),(name,f"/practices/{slug}/")],body)))
    for cslug,cname,angle,emph,ckw in CITIES:
        rm=recent_section(recent_moves(arts,None,ckw))
        prac_links=live([(f"{PRAC[ps][1]} in {cname}",f"/practices/{ps}/{cslug}/") for ps in [p[0] for p in PRACTICES]], rel)
        emph_names=", ".join(PRAC[e][1] for e in emph)
        faqs=[(f"Do you recruit partners in {cname}?",f"Yes. We run confidential partner and group searches across practices with AmLaw 200 firms and boutiques in {cname} and nationwide."),
              (f"Which practices are most active in {cname}?",f"In {cname} we see particular activity in {emph_names}, though we cover the full range of practices."),
              ("Do you represent firms or candidates?","Both. We run retained searches for firms and represent partners and groups exploring a move.")]
        body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">{cname[:2].upper()}</span> Market</span><h1 class="section-title">Legal recruiting in <em>{esc(cname)}.</em></h1>'
          f'<p class="section-lede">{esc(cname)} is {esc(angle)}. We represent partners and practice groups on confidential lateral moves to AmLaw 200 firms and leading boutiques in {esc(cname)}, with particular depth in {esc(emph_names)}.</p></div>{ctas(cname.split(",")[0].replace(" ","%20"))}</section>'
          f'{related_section("01","Practices in "+cname,"Searches we run <em>here.</em>",prac_links)}'
          f'{rm}'
          f'<section class="section approach" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">02</span> The Process</span><h2 class="section-title">Three steps, <em>handled end to end.</em></h2></div>{process()}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">03</span> Questions</span><h2 class="section-title">{esc(cname)} moves, <em>answered.</em></h2></div>{faq_block(faqs)}</section>')
        pages.append((f"markets/{cslug}/index.html", page(f"Legal Recruiters in {cname} | Lionpoint Partners",
            f"Lionpoint Partners recruits partners and practice groups for AmLaw 200 firms and boutiques in {cname}. Confidential lateral search.",
            DOMAIN+f"/markets/{cslug}/",[("Home","/"),("Markets","/markets/"),(cname,f"/markets/{cslug}/")],body)))
    for cslug,cname,angle,emph,ckw in CITIES:
        for slug,name,kw,items,mkt,pkw in PRACTICES:
            rm=recent_section(recent_moves(arts,pkw,ckw))
            note=(f"It is one of the practices we see hiring most actively in {cname}." if slug in emph else f"Demand moves with the local market, and a portable book travels well in {cname}.")
            sibs=live([(f"{PRAC[ps][1]} in {cname}",f"/practices/{ps}/{cslug}/") for ps in emph if ps!=slug][:3], rel)
            rl=[(f"All {name} searches",f"/practices/{slug}/"),(f"All {cname} searches",f"/markets/{cslug}/")]+sibs
            faqs=[(f"Do you recruit {kw} partners in {cname}?",f"Yes. We run confidential {kw} partner and group searches with AmLaw 200 firms and boutiques in {cname} and nationwide."),
                  (f"What makes {cname} distinct for {kw}?",f"{cname} is {angle}, which shapes where the demand sits and which firms are hiring in {kw}."),
                  (f"How portable does my book need to be to move in {cname}?",f"Portability matters more than a number. We give you an honest read on how your {cname} {kw} practice and relationships are likely to be valued.")]
            body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">{cname[:2].upper()}</span> {esc(name)} &middot; {esc(cname)}</span><h1 class="section-title">{esc(name)} partner recruiting in <em>{esc(cname)}.</em></h1>'
              f'<p class="section-lede">We represent {esc(kw)} partners and practice groups on confidential lateral moves in {esc(cname)}, a market that is {esc(angle)}. Every search is led by a recruiter who knows both the {esc(kw)} market and the {esc(cname)} firms hiring in it.</p></div>{ctas(name.replace(" ","%20").replace("&","and"))}</section>'
              f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">01</span> What we handle</span><h2 class="section-title">{esc(name)} searches in <em>{esc(cname)}.</em></h2></div>{services(items)}</section>'
              f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">02</span> The {esc(cname)} market</span><h2 class="section-title">Where {esc(kw)} is <em>moving.</em></h2><p class="section-lede">{esc(mkt)} {esc(note)}</p></div></section>'
              f'{rm}'
              f'<section class="section approach" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">03</span> The Process</span><h2 class="section-title">Three steps, <em>handled end to end.</em></h2></div>{process()}</section>'
              f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">04</span> Questions</span><h2 class="section-title">{esc(name)} in {esc(cname)}, <em>answered.</em></h2></div>{faq_block(faqs)}</section>'
              f'{related_section("05","Related searches","Explore <em>more.</em>",rl)}')
            pages.append((f"practices/{slug}/{cslug}/index.html", page(f"{name} Partner Recruiting in {cname} | Lionpoint Partners",
                f"{name} partner and group recruiting in {cname}. Confidential lateral search with AmLaw 200 firms and boutiques. Lionpoint Partners.",
                DOMAIN+f"/practices/{slug}/{cslug}/",[("Home","/"),("Practices","/practices/"),(name,f"/practices/{slug}/"),(cname,f"/practices/{slug}/{cslug}/")],body)))
    return pages

CSS='''.pmx-page{background:var(--bg);color:var(--ink)}
.pmx-page .nav{position:sticky;top:0;background:rgba(244,238,226,.85);backdrop-filter:blur(8px);z-index:50}
.faq{max-width:var(--maxw);margin:0 auto;border-top:1px solid var(--line)}
.faq-item{padding:24px 0;border-bottom:1px solid var(--line)}
.faq-item h3{font-family:var(--font-display);font-weight:400;font-size:clamp(18px,2vw,24px);letter-spacing:-0.01em;margin:0 0 8px}
.faq-item p{color:var(--ink-dim);font-size:16px;line-height:1.7;margin:0;max-width:780px}
.pmx-wrap a[href]{}
.rel-wrap{max-width:var(--maxw);margin:0 auto}
.rel-eyebrow{font-family:var(--font-mono);font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:var(--ink-mute);margin-bottom:16px}
.rel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0;border-top:1px solid var(--line);border-left:1px solid var(--line)}
.rel{display:block;padding:16px 18px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);font-family:var(--font-sans);font-size:14px;line-height:1.4;color:var(--ink-dim);text-decoration:none;background:var(--bg);transition:background .3s,color .3s}
.rel:hover{background:var(--bg-3);color:var(--accent)}
.rel-date{display:block;font-family:var(--font-mono);font-size:11px;color:var(--ink-mute);margin-bottom:5px}
.pmx-foot{border-top:1px solid var(--line);margin-top:40px}
.pmx-foot .foot-bottom{max-width:var(--maxw);margin:0 auto;padding:28px var(--pad);display:flex;flex-wrap:wrap;gap:14px 28px;justify-content:space-between;font-family:var(--font-mono);font-size:12px;color:var(--ink-mute)}
.pmx-foot a{color:var(--ink-dim);text-decoration:none}.pmx-foot a:hover{color:var(--accent)}
'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",required=True); ap.add_argument("--advance",type=int,default=0); ap.add_argument("--release-all",action="store_true")
    a=ap.parse_args()
    order=page_order(); total=len(order)
    mf=os.path.join(a.repo,"seo-release.json"); released=0
    if os.path.exists(mf):
        try: released=json.load(open(mf)).get("released",0)
        except: released=0
    released = total if a.release_all else min(total, released+max(0,a.advance))
    rel=set(order[:released])
    pages=build_all(a.repo, rel)
    bypath={p:h for p,h in pages}
    for path in order[:released]:
        full=os.path.join(a.repo,path); os.makedirs(os.path.dirname(full),exist_ok=True)
        open(full,"w",encoding="utf-8").write(bypath[path])
    open(os.path.join(a.repo,"practices.css"),"w").write(CSS)
    sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm+="".join(f'  <url><loc>{DOMAIN}/{path.replace("index.html","")}</loc></url>\n' for path in order[:released])+"</urlset>\n"
    open(os.path.join(a.repo,"sitemap-seo.xml"),"w").write(sm)
    json.dump({"released":released,"total":total},open(mf,"w"))
    print(f"released {released}/{total}")

if __name__=="__main__": main()
