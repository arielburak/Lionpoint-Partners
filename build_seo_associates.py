#!/usr/bin/env python3
"""Associate-side SEO pages, reusing the partner generator's templates.
URLs: /associates/, /associates/practices/<p>/, /associates/markets/<c>/, /associates/practices/<p>/<c>/
Drip-release via seo-release-assoc.json; sitemap-associates.xml. Same Recent moves from Market Pulse."""
import importlib.util, os, json, argparse
_here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location("bs", os.path.join(_here,"build_seo.py"))
bs=importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
DOMAIN=bs.DOMAIN; M=bs.M; PRACTICES=bs.PRACTICES; CITIES=bs.CITIES; PRAC=bs.PRAC
esc=bs.esc; page=bs.page; services=bs.services; process=bs.process; faq_block=bs.faq_block
related=bs.related; related_section=bs.related_section; recent_section=bs.recent_section
recent_moves=bs.recent_moves; parse_pulse=bs.parse_pulse; ctas=bs.ctas; live=bs.live

ITEMS=["Associates at every level, junior through senior","Counsel-track and specialist associates",
       "Lateral associates seeking better work, training, or culture","Associate groups moving together"]
def amkt(kw): return (f"In {kw}, firms hire laterally for associates with strong training and real "
    f"experience, and the best moves line up the work, the mentorship, and a clear path to partnership.")

def page_order():
    o=["associates/index.html"]
    o+=[f"associates/practices/{p[0]}/index.html" for p in PRACTICES]
    o+=[f"associates/markets/{c[0]}/index.html" for c in CITIES]
    o+=[f"associates/practices/{p[0]}/{c[0]}/index.html" for c in CITIES for p in PRACTICES]
    return o

def build_all(repo, rel):
    arts=parse_pulse(repo); pages=[]
    pl=live([(p[1]+" Associate Recruiting",f"/associates/practices/{p[0]}/") for p in PRACTICES], rel)
    cl=live([("Associate Recruiting in "+c[1],f"/associates/markets/{c[0]}/") for c in CITIES], rel)
    body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">00</span> Associates</span>'
        f'<h2 class="section-title">Associate <em>recruiting.</em></h2><p class="section-lede">We place associates, from junior to senior, at AmLaw 200 firms and leading boutiques where the work, training, and trajectory genuinely fit. Browse by practice or by market.</p></div>'
        f'<section style="padding-top:0">{related("By practice",pl)}</section>'
        f'<section style="padding-top:0">{related("By market",cl)}</section></section>')
    pages.append(("associates/index.html", page("Legal Associate Recruiting | Lionpoint Partners",
        "Confidential associate placement across M&A, private equity, real estate, litigation, finance, IP, and more, for AmLaw 200 firms nationwide.",
        DOMAIN+"/associates/",[("Home","/"),("Associates","/associates/")],body)))
    for slug,name,kw,items,mkt,pkw in PRACTICES:
        city_links=live([(f"{name} associates in {c[1]}",f"/associates/practices/{slug}/{c[0]}/") for c in CITIES], rel)
        faqs=[(f"Do you place {kw} associates confidentially?","Yes. Every search is confidential and nothing goes out without your approval."),
              ("What associate levels do you work with?","Junior through senior associates, including counsel-track and specialist roles."),
              ("How do you match associates to firms?","We look past the brochure at the work, the training, the team, and the path to partnership, so the move actually fits.")]
        body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">AS</span> Associate Focus</span><h1 class="section-title">{esc(name)} associate <em>recruiting.</em></h1>'
          f'<p class="section-lede">We place {esc(kw)} associates, from junior to senior, at AmLaw 200 firms and leading boutiques where the work, training, and trajectory genuinely fit. Confidential, with no pressure to take a seat that is not right for you.</p></div>{ctas(name.replace(" ","%20").replace("&","and")+"%20Associate")}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">01</span> What we handle</span><h2 class="section-title">{esc(name)} associates, <em>every level.</em></h2></div>{services(ITEMS)}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">02</span> The market</span><h2 class="section-title">Where associates are <em>moving.</em></h2><p class="section-lede">{esc(amkt(kw))}</p></div></section>'
          f'<section class="section approach" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">03</span> The Process</span><h2 class="section-title">Three steps, <em>handled end to end.</em></h2></div>{process()}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">04</span> Questions</span><h2 class="section-title">{esc(name)} associate moves, <em>answered.</em></h2></div>{faq_block(faqs)}</section>'
          f'{related_section("05","Where we recruit",esc(name)+" associates by <em>city.</em>",city_links)}')
        pages.append((f"associates/practices/{slug}/index.html", page(f"{name} Associate Recruiting | Lionpoint Partners",
            f"Lionpoint Partners places {kw} associates, junior to senior, at AmLaw 200 firms and boutiques nationwide. Confidential lateral search.",
            DOMAIN+f"/associates/practices/{slug}/",[("Home","/"),("Associates","/associates/"),(name,f"/associates/practices/{slug}/")],body)))
    for cslug,cname,angle,emph,ckw in CITIES:
        prac_links=live([(f"{PRAC[ps][1]} associates in {cname}",f"/associates/practices/{ps}/{cslug}/") for ps in [p[0] for p in PRACTICES]], rel)
        emph_names=", ".join(PRAC[e][1] for e in emph)
        faqs=[(f"Do you place associates in {cname}?",f"Yes. We run confidential associate searches across practices with AmLaw 200 firms and boutiques in {cname} and nationwide."),
              (f"Which practices hire associates most in {cname}?",f"In {cname} we see particular associate activity in {emph_names}, though we cover the full range."),
              ("How do you match associates to firms?","We weigh the work, training, team, hours, and partnership path, not just the name on the door.")]
        body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">{cname[:2].upper()}</span> Market</span><h1 class="section-title">Associate recruiting in <em>{esc(cname)}.</em></h1>'
          f'<p class="section-lede">{esc(cname)} is {esc(angle)}. We place associates, junior to senior, at AmLaw 200 firms and leading boutiques in {esc(cname)}, with particular depth in {esc(emph_names)}.</p></div>{ctas(cname.split(",")[0].replace(" ","%20")+"%20Associate")}</section>'
          f'{related_section("01","Practices in "+cname,"Associate searches we run <em>here.</em>",prac_links)}'
          f'<section class="section approach" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">02</span> The Process</span><h2 class="section-title">Three steps, <em>handled end to end.</em></h2></div>{process()}</section>'
          f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">03</span> Questions</span><h2 class="section-title">{esc(cname)} associate moves, <em>answered.</em></h2></div>{faq_block(faqs)}</section>')
        pages.append((f"associates/markets/{cslug}/index.html", page(f"Associate Recruiters in {cname} | Lionpoint Partners",
            f"Lionpoint Partners places associates at AmLaw 200 firms and boutiques in {cname}. Confidential lateral associate search.",
            DOMAIN+f"/associates/markets/{cslug}/",[("Home","/"),("Associates","/associates/"),(cname,f"/associates/markets/{cslug}/")],body)))
    for cslug,cname,angle,emph,ckw in CITIES:
        for slug,name,kw,items,mkt,pkw in PRACTICES:
            sibs=live([(f"{PRAC[ps][1]} associates in {cname}",f"/associates/practices/{ps}/{cslug}/") for ps in emph if ps!=slug][:3], rel)
            rl=[(f"All {name} associate searches",f"/associates/practices/{slug}/"),(f"All {cname} associate searches",f"/associates/markets/{cslug}/")]+sibs
            faqs=[(f"Do you place {kw} associates in {cname}?",f"Yes. We run confidential {kw} associate searches with AmLaw 200 firms and boutiques in {cname} and nationwide."),
                  (f"What is the {cname} market like for {kw} associates?",f"{cname} is {angle}, which shapes which firms are hiring {kw} associates and at what levels."),
                  (f"How do you decide if a {cname} firm is the right fit?","We weigh the work, training, team, hours, and partnership path, so the move actually fits your goals.")]
            body=(f'<section class="section"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">{cname[:2].upper()}</span> {esc(name)} &middot; {esc(cname)}</span><h1 class="section-title">{esc(name)} associate recruiting in <em>{esc(cname)}.</em></h1>'
              f'<p class="section-lede">We place {esc(kw)} associates, junior to senior, at firms in {esc(cname)}, a market that is {esc(angle)}. We look past the brochure to the work, the training, and the path to partnership.</p></div>{ctas(name.replace(" ","%20").replace("&","and")+"%20Associate")}</section>'
              f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">01</span> What we handle</span><h2 class="section-title">{esc(name)} associates in <em>{esc(cname)}.</em></h2></div>{services(ITEMS)}</section>'
              f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">02</span> The {esc(cname)} market</span><h2 class="section-title">Where {esc(kw)} associates are <em>moving.</em></h2><p class="section-lede">{esc(amkt(kw))}</p></div></section>'
                  f'<section class="section approach" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">03</span> The Process</span><h2 class="section-title">Three steps, <em>handled end to end.</em></h2></div>{process()}</section>'
              f'<section class="section" style="padding-top:0"><div class="section-head"><span class="eyebrow"><span class="eyebrow-num">04</span> Questions</span><h2 class="section-title">{esc(name)} associates in {esc(cname)}, <em>answered.</em></h2></div>{faq_block(faqs)}</section>'
              f'{related_section("05","Related searches","Explore <em>more.</em>",rl)}')
            pages.append((f"associates/practices/{slug}/{cslug}/index.html", page(f"{name} Associate Recruiting in {cname} | Lionpoint Partners",
                f"{name} associate recruiting in {cname}. Confidential lateral search with AmLaw 200 firms and boutiques. Lionpoint Partners.",
                DOMAIN+f"/associates/practices/{slug}/{cslug}/",[("Home","/"),("Associates","/associates/"),(name,f"/associates/practices/{slug}/"),(cname,f"/associates/practices/{slug}/{cslug}/")],body)))
    return pages

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",required=True); ap.add_argument("--advance",type=int,default=0); ap.add_argument("--release-all",action="store_true")
    a=ap.parse_args(); order=page_order(); total=len(order)
    mf=os.path.join(a.repo,"seo-release-assoc.json"); released=0
    if os.path.exists(mf):
        try: released=json.load(open(mf)).get("released",0)
        except: released=0
    released= total if a.release_all else min(total, released+max(0,a.advance))
    rel=set(order[:released]); pages=build_all(a.repo, rel); bypath={p:h for p,h in pages}
    for path in order[:released]:
        full=os.path.join(a.repo,path); os.makedirs(os.path.dirname(full),exist_ok=True); open(full,"w",encoding="utf-8").write(bypath[path])
    sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm+="".join(f'  <url><loc>{DOMAIN}/{p.replace("index.html","")}</loc></url>\n' for p in order[:released])+"</urlset>\n"
    open(os.path.join(a.repo,"sitemap-associates.xml"),"w").write(sm)
    json.dump({"released":released,"total":total},open(mf,"w")); print(f"associate pages released {released}/{total}")

if __name__=="__main__": main()
