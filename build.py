#!/usr/bin/env python3
# ECG Means static site generator
# Reads content/*.txt (delimited @@FIELD@@ format), emits a full static site into site/
# with upgraded <head>, @graph JSON-LD, OG/Twitter, breadcrumbs, FAQ schema, sitemaps,
# robots.txt, llms.txt, llms-full.txt, .htaccess, index.php 404 shim, 404.html and assets.
import os, re, html, json, datetime, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "site")

SITE = "ECG Means"
HOST = "https://www.ecgmeans.com"
TAGLINE = "Your ECG report, explained in plain English"
BRAND = "#b91c1c"
PUBLISHED = "2026-09-21"
MODIFIED = "2026-10-01"
REVIEWER = "Dr. Faisal Irshad"
REVIEWER_SUFFIX = "MBBS"
REVIEWER_TITLE = "Medical Doctor"
PMDC = "PMDC 54440-S"
CONTACT_EMAIL = "hello@ecgmeans.com"
OG_IMG = HOST + "/assets/img/og-default.png"
# Set to your AdSense publisher id (e.g. "ca-pub-1234567890123456") to enable Auto Ads.
AD_CLIENT = ""
# Optional: Google Search Console verification token (meta-tag method). Leave "" to omit.
GSC_VERIFY = ""

import markdown as mdlib

HUBS = [
    ("ecg-report-phrases", "Report phrases", "ECG Report Phrases", "MedicalSignOrSymptom"),
    ("heart-rhythms", "Rhythms", "Heart Rhythms", "MedicalSignOrSymptom"),
    ("heart-block-conduction", "Blocks", "Heart Blocks & Conduction", "MedicalSignOrSymptom"),
    ("ecg-intervals-waves", "Intervals", "Intervals & Waves", "MedicalSignOrSymptom"),
    ("ecg-comparisons", "Comparisons", "Comparisons", "MedicalTest"),
    ("ecg-basics", "Basics", "ECG Basics", "MedicalTest"),
]
HUB_SLUGS = [h[0] for h in HUBS]
HUB_LABEL = {h[0]: h[2] for h in HUBS}
HUB_ABOUT = {h[0]: h[3] for h in HUBS}
POLICY = ["about", "privacy", "disclaimer", "contact"]
HOME = "index"
VERDICTS = {
    "Usually harmless": "ok",
    "Depends on context": "warn",
    "Needs clinician review": "review",
    "Seek prompt care": "urgent",
}

def esc(s): return html.escape(s or "", quote=True)

def read_fields(path):
    t = open(path, encoding="utf-8").read()
    fields = {}
    for m in re.finditer(r'@@([A-Z0-9]+)@@\n(.*?)(?=\n@@[A-Z0-9]+@@|\Z)', t, re.S):
        fields[m.group(1)] = m.group(2).strip()
    fields.pop("END", None)
    return fields

def parse_pipe_lines(block):
    rows = []
    for line in (block or "").splitlines():
        line = line.strip()
        if not line or line.upper() == "NONE":
            continue
        parts = [p.strip() for p in line.split("|")]
        rows.append(parts)
    return rows

def parse_faq(block):
    out = []
    q = None
    for line in (block or "").splitlines():
        line = line.rstrip()
        if line.startswith("Q:"):
            q = line[2:].strip()
        elif line.startswith("A:") and q is not None:
            out.append((q, line[2:].strip()))
            q = None
    return out

def render_md(text):
    md = mdlib.Markdown(extensions=["tables", "sane_lists", "toc"])
    body = md.convert(text or "")
    # urgent callout
    body = body.replace("<p><strong>Get urgent help</strong>",
                        '<p class="callout callout-urgent"><strong>Get urgent help</strong>')
    # collect H2 headings for TOC
    heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    return body, heads

def jsonld_graph(nodes):
    g = {"@context": "https://schema.org", "@graph": nodes}
    return '<script type="application/ld+json">' + json.dumps(g, ensure_ascii=False) + '</script>'

ORG_NODE = {
    "@type": ["Organization", "MedicalOrganization"], "@id": HOST + "/#org",
    "name": SITE, "url": HOST + "/",
    "logo": {"@type": "ImageObject", "url": HOST + "/assets/img/logo.png", "width": 512, "height": 512},
    "description": "Independent, clinician-reviewed plain-English explanations of ECG/EKG report phrases.",
    "email": CONTACT_EMAIL,
}
WEBSITE_NODE = {
    "@type": "WebSite", "@id": HOST + "/#website", "name": SITE, "url": HOST + "/",
    "publisher": {"@id": HOST + "/#org"}, "inLanguage": "en",
    "potentialAction": {"@type": "SearchAction",
        "target": {"@type": "EntryPoint", "urlTemplate": HOST + "/?q={search_term_string}"},
        "query-input": "required name=search_term_string"},
}
AUTHOR_NODE = {
    "@type": "Person", "@id": HOST + "/#author", "name": REVIEWER,
    "honorificSuffix": REVIEWER_SUFFIX, "jobTitle": REVIEWER_TITLE,
    "identifier": PMDC, "url": HOST + "/about/",
    "description": "Medical doctor (MBBS) with 18 years of clinical and laboratory-medicine experience.",
}

def head(title, desc, canonical, og_type, extra_nodes):
    nodes = [ORG_NODE, WEBSITE_NODE, AUTHOR_NODE] + extra_nodes
    ads = ""
    if AD_CLIENT:
        ads = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='
               + AD_CLIENT + '" crossorigin="anonymous"></script>')
    verify = ('<meta name="google-site-verification" content="' + GSC_VERIFY + '">\n') if GSC_VERIFY else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">
<meta name="author" content="{esc(REVIEWER)}, {REVIEWER_SUFFIX}">
<meta name="theme-color" content="{BRAND}">
{verify}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{OG_IMG}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/icon-180.png">
<link rel="stylesheet" href="/assets/css/style.css">
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
{ads}{jsonld_graph(nodes)}
</head>'''

def header_html():
    nav = "\n".join(
        f'<a href="/{s}/">{esc(lbl)}</a>' for s, lbl, *_ in HUBS)
    return f'''<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="/" aria-label="ECG Means home">
<svg class="mark" viewBox="0 0 64 64" width="30" height="30" aria-hidden="true"><rect width="64" height="64" rx="12" fill="{BRAND}"/><path d="M6 36h12l6-16 8 30 8-22 4 8h14" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/></svg>
<span>ECG&nbsp;Means</span></a>
<button class="menu-btn" aria-label="Menu" aria-expanded="false" onclick="var n=document.getElementById('nav'),o=n.classList.toggle('open');this.setAttribute('aria-expanded',o)">☰</button>
<nav class="nav" id="nav" aria-label="Primary">
{nav}
</nav>
</div></header>'''

def footer_html():
    return f'''<footer class="site-foot"><div class="wrap">
<p class="foot-brand"><strong>{SITE}</strong> — {TAGLINE}<br>Reviewed by {esc(REVIEWER)}, {REVIEWER_SUFFIX} · {REVIEWER_TITLE} · {PMDC}</p>
<nav class="foot-links" aria-label="Footer">
<a href="/about/">About &amp; editorial policy</a>
<a href="/privacy/">Privacy</a>
<a href="/disclaimer/">Medical disclaimer</a>
<a href="/contact/">Contact</a>
</nav>
<p class="foot-note">ECG Means provides general educational information about electrocardiogram findings. It is not medical advice and cannot interpret your individual ECG. Always discuss your results with the clinician who ordered the test. If you have chest pain, severe breathlessness or fainting, seek emergency care.</p>
<p class="copyright">© 2026 ECG Means. Last reviewed {MODIFIED}.</p>
</div></footer>
</body>
</html>'''

def ad_unit():
    if not AD_CLIENT:
        return ""
    return (f'<div class="ad"><ins class="adsbygoogle" style="display:block" '
            f'data-ad-client="{AD_CLIENT}" data-ad-format="fluid" data-ad-layout="in-article"></ins>'
            f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')

def byline(updated=MODIFIED):
    return (f'<div class="byline"><span class="rev">Medically reviewed by <strong>{esc(REVIEWER)}, {REVIEWER_SUFFIX}</strong> · {REVIEWER_TITLE}</span>'
            f'<span class="meta">{PMDC}</span><span class="meta">Updated {updated}</span></div>')

def breadcrumbs_html(trail):
    # trail: list of (name, url_or_None)
    parts = []
    for name, url in trail:
        if url:
            parts.append(f'<a href="{url}">{esc(name)}</a>')
        else:
            parts.append(f'<span aria-current="page">{esc(name)}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + ' <span class="sep">›</span> '.join(parts) + '</nav>'

def breadcrumb_jsonld(trail):
    items = []
    for i, (name, url) in enumerate(trail, 1):
        it = {"@type": "ListItem", "position": i, "name": name}
        if url:
            it["item"] = url if url.startswith("http") else HOST + url
        items.append(it)
    return {"@type": "BreadcrumbList", "itemListElement": items}

def faq_jsonld(faqs):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}

def verdict_badge(quick):
    cls = VERDICTS.get(quick)
    if cls:
        return f'<span class="verdict verdict-{cls}">{esc(quick)}</span>'
    return ""

def write_page(rel_path, html_text):
    d = os.path.join(OUT, rel_path.strip("/"))
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html_text)

# ---------- load all content ----------
pages = {}
for fn in os.listdir(CONTENT):
    if fn.endswith(".txt"):
        pages[fn[:-4]] = read_fields(os.path.join(CONTENT, fn))

content_slugs = [s for s in pages if s not in HUB_SLUGS and s not in POLICY and s != HOME]

# map content slug -> hub slug via CATEGORY url
slug_hub = {}
hub_members = {h: [] for h in HUB_SLUGS}
for s in content_slugs:
    cat = pages[s].get("CATEGORY", "")
    hub = None
    m = re.search(r'/([a-z0-9-]+)/\s*$', cat.split("|")[-1].strip()) if "|" in cat else None
    if m and m.group(1) in HUB_SLUGS:
        hub = m.group(1)
    slug_hub[s] = hub
    if hub:
        hub_members[hub].append(s)

# order members by original sitemap-ish order: keep as encountered but sort by title for stability within hub? keep insertion; we'll sort later per hub by a defined order
for h in hub_members:
    hub_members[h].sort(key=lambda s: pages[s].get("H1", s).lower())

def short_title(s):
    # Prefer H1 trimmed of trailing ": What It Means..." for cards
    h1 = pages[s].get("H1", s)
    return h1

def page_card(s):
    f = pages[s]
    quick = f.get("QUICK", "").strip()
    badge = verdict_badge(quick)
    return (f'<li class="card"><a href="/{s}/"><span class="card-t">{esc(f.get("H1", s))}</span>'
            f'{badge}</a></li>')

# ---------- render content pages ----------
def render_content(s):
    f = pages[s]
    title = f.get("TITLE", f.get("H1", s))
    desc = f.get("DESC", "")
    h1 = f.get("H1", s)
    quick = f.get("QUICK", "").strip()
    lede = f.get("LEDE", "").strip()
    body_md = f.get("BODY", "")
    faqs = parse_faq(f.get("FAQ", ""))
    related = parse_pipe_lines(f.get("RELATED", ""))
    sources = parse_pipe_lines(f.get("SOURCES", ""))
    also = f.get("ALSO", "").strip()
    canonical = f"{HOST}/{s}/"
    hub = slug_hub.get(s)
    hub_label = HUB_LABEL.get(hub, "ECG findings")
    trail = [("Home", "/"), (hub_label, f"/{hub}/" if hub else "/"), (h1_crumb(h1), None)]

    body_html, heads = render_md(body_md)

    # answer / badge logic
    answer_box = ""
    show_lede = True
    badge = verdict_badge(quick)
    if quick and quick not in VERDICTS and quick.upper() != "NONE" and len(quick) > 40:
        # long-form quick answer -> callout
        answer_box = f'<div class="answer"><div class="answer-k">Quick answer</div><p>{esc(quick)}</p></div>'
        # dedupe lede if it repeats the quick answer
        if lede[:50].lower() == quick[:50].lower():
            show_lede = False

    toc = ""
    if len(heads) >= 3:
        lis = "\n".join(f'<li><a href="#{hid}">{re.sub("<[^>]+>","",htxt)}</a></li>' for hid, htxt in heads)
        toc = f'<nav class="toc" aria-label="On this page"><div class="toc-k">On this page</div><ol>{lis}</ol></nav>'

    faq_html = ""
    if faqs:
        items = "\n".join(
            f'<div class="faq-item"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in faqs)
        faq_html = f'<section class="faq" id="faq"><h2>Frequently asked questions</h2>{items}</section>'

    also_html = ""
    if also and also.upper() != "NONE":
        also_clean = re.sub(r'^Also searched as:\s*', '', also).strip().rstrip('.')
        also_html = f'<p class="also"><span>Also searched as:</span> {esc(also_clean)}.</p>'

    related_html = ""
    if related:
        lis = []
        for r in related:
            anchor = r[0]; url = r[1] if len(r) > 1 else "#"
            note = r[2] if len(r) > 2 and r[2].upper() != "NONE" else ""
            path = re.sub(r'^https?://www\.ecgmeans\.com', '', url)
            nb = f'<span class="rel-note">{esc(note)}</span>' if note else ""
            lis.append(f'<li><a href="{path}">{esc(anchor)}</a>{nb}</li>')
        related_html = f'<section class="related"><h2>Related ECG findings</h2><ul class="rel-list">{"".join(lis)}</ul></section>'

    sources_html = ""
    if sources:
        lis = []
        for r in sources:
            t = r[0]; url = r[1] if len(r) > 1 else "#"
            lis.append(f'<li><a href="{esc(url)}" rel="nofollow noopener" target="_blank">{esc(t)}</a></li>')
        sources_html = f'<section class="sources"><h2>Sources</h2><ol>{"".join(lis)}</ol></section>'

    # schema
    mwp = {
        "@type": "MedicalWebPage", "@id": canonical + "#webpage",
        "name": title, "headline": h1, "description": desc, "url": canonical,
        "inLanguage": "en", "datePublished": PUBLISHED, "dateModified": MODIFIED,
        "isPartOf": {"@id": HOST + "/#website"},
        "about": {"@type": HUB_ABOUT.get(hub, "MedicalSignOrSymptom"), "name": h1_crumb(h1)},
        "author": {"@id": HOST + "/#author"},
        "reviewedBy": {"@id": HOST + "/#author"},
        "lastReviewed": MODIFIED,
        "publisher": {"@id": HOST + "/#org"},
        "medicalAudience": {"@type": "MedicalAudience", "audienceType": "Patient"},
        "primaryImageOfPage": {"@type": "ImageObject", "url": OG_IMG},
    }
    nodes = [mwp, breadcrumb_jsonld(trail)]
    if faqs:
        nodes.append(faq_jsonld(faqs))

    lede_html = f'<p class="lede">{esc(lede)}</p>' if (lede and show_lede) else ""
    badge_html = f'<div class="verdict-row">{badge}</div>' if badge else ""

    article = f'''{breadcrumbs_html(trail)}
<article>
<h1>{esc(h1)}</h1>
{badge_html}
{lede_html}
{byline()}
{answer_box}
{ad_unit()}
{toc}
<div class="body">
{body_html}
</div>
{faq_html}
{also_html}
{related_html}
{sources_html}
</article>'''

    return head(title, desc, canonical, "article", nodes) + header_html() + \
        f'<main id="main" class="wrap narrow">{article}</main>' + footer_html()

def h1_crumb(h1):
    # short label for breadcrumb/about
    return re.split(r':|\(|\u2014| on an| on your| on the', h1)[0].strip()

# ---------- render hubs ----------
def render_hub(s):
    f = pages[s]
    title = f.get("TITLE", f.get("H1", s))
    desc = f.get("DESC", "")
    h1 = f.get("H1", s)
    lede = f.get("LEDE", "").strip()
    canonical = f"{HOST}/{s}/"
    label = HUB_LABEL[s]
    members = hub_members.get(s, [])
    cards = "\n".join(page_card(m) for m in members)
    # other hubs nav
    others = "\n".join(
        f'<li><a href="/{h}/"><span class="card-t">{esc(HUB_LABEL[h])}</span></a></li>'
        for h in HUB_SLUGS if h != s)
    trail = [("Home", "/"), (label, None)]
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{HOST}/{m}/", "name": pages[m].get("H1", m)}
        for i, m in enumerate(members)]}
    collection = {
        "@type": "CollectionPage", "@id": canonical + "#webpage",
        "name": title, "description": desc, "url": canonical, "inLanguage": "en",
        "isPartOf": {"@id": HOST + "/#website"}, "about": {"@id": HOST + "/#org"},
        "dateModified": MODIFIED, "mainEntity": item_list,
    }
    nodes = [collection, breadcrumb_jsonld(trail)]
    main = f'''{breadcrumbs_html(trail)}
<article>
<h1>{esc(h1)}</h1>
<p class="lede">{esc(lede)}</p>
{byline()}
{ad_unit()}
<ul class="cards">
{cards}
</ul>
<section class="other-hubs"><h2>More ECG topics</h2><ul class="cards">
{others}
</ul></section>
</article>'''
    return head(title, desc, canonical, "website", nodes) + header_html() + \
        f'<main id="main" class="wrap">{main}</main>' + footer_html()

# ---------- render policy ----------
def render_policy(s):
    f = pages[s]
    title = f.get("TITLE", f.get("H1", s))
    desc = f.get("DESC", "")
    h1 = f.get("H1", s)
    lede = f.get("LEDE", "").strip()
    body_html, _ = render_md(f.get("BODY", ""))
    canonical = f"{HOST}/{s}/"
    trail = [("Home", "/"), (h1, None)]
    wp = {"@type": "WebPage", "@id": canonical + "#webpage", "name": title,
          "description": desc, "url": canonical, "inLanguage": "en",
          "isPartOf": {"@id": HOST + "/#website"}, "dateModified": MODIFIED}
    if s == "about":
        wp = {"@type": "AboutPage", "@id": canonical + "#webpage", "name": title,
              "description": desc, "url": canonical, "inLanguage": "en",
              "isPartOf": {"@id": HOST + "/#website"}, "dateModified": MODIFIED,
              "mainEntity": {"@id": HOST + "/#author"}}
    nodes = [wp, breadcrumb_jsonld(trail)]
    main = f'''{breadcrumbs_html(trail)}
<article>
<h1>{esc(h1)}</h1>
<p class="lede">{esc(lede)}</p>
<div class="body">
{body_html}
</div>
</article>'''
    return head(title, desc, canonical, "website", nodes) + header_html() + \
        f'<main id="main" class="wrap narrow">{main}</main>' + footer_html()

# ---------- render home ----------
def render_home():
    f = pages[HOME]
    title = f.get("TITLE")
    desc = f.get("DESC")
    h1 = f.get("H1")
    lede = f.get("LEDE", "").strip()
    body_html, _ = render_md(f.get("BODY", ""))
    canonical = HOST + "/"
    # search index
    idx = [{"t": pages[s].get("H1", s), "u": f"/{s}/", "v": pages[s].get("QUICK", "").strip(),
            "k": (pages[s].get("ALSO", "") + " " + pages[s].get("H1", "")).lower()}
           for s in content_slugs]
    idx_json = json.dumps(idx, ensure_ascii=False)
    # hub cards
    hubcards = "\n".join(
        f'<li class="hubcard"><a href="/{h}/"><span class="hc-t">{esc(HUB_LABEL[h])}</span>'
        f'<span class="hc-d">{esc(pages[h].get("DESC",""))}</span>'
        f'<span class="hc-n">{len(hub_members[h])} pages</span></a></li>'
        for h in HUB_SLUGS)
    # A-Z list
    az = sorted(content_slugs, key=lambda s: pages[s].get("H1", s).lower())
    azlist = "\n".join(page_card(s) for s in az)
    nodes = [{"@type": "WebPage", "@id": canonical + "#webpage", "name": title,
              "description": desc, "url": canonical, "isPartOf": {"@id": HOST + "/#website"},
              "inLanguage": "en", "dateModified": MODIFIED}]
    search = f'''<div class="hero">
<h1>{esc(h1)}</h1>
<p class="lede">{esc(lede)}</p>
<div class="search"><input type="search" id="q" placeholder="Search your ECG phrase… e.g. borderline ECG" aria-label="Search ECG phrases" autocomplete="off">
<ul id="results" class="results" hidden></ul></div>
</div>'''
    main = f'''{search}
{ad_unit()}
<section class="hubs-section"><h2>Browse by topic</h2>
<ul class="hubcards">{hubcards}</ul></section>
<section class="how">{body_html}</section>
<section class="az"><h2>All ECG report phrases, A–Z</h2>
<ul class="cards">{azlist}</ul></section>
<script>
const IDX={idx_json};
const q=document.getElementById('q'),res=document.getElementById('results');
function esc(s){{return s.replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));}}
q&&q.addEventListener('input',function(){{
 const v=this.value.trim().toLowerCase();
 if(!v){{res.hidden=true;res.innerHTML='';return;}}
 const hits=IDX.filter(x=>x.k.includes(v)||x.t.toLowerCase().includes(v)).slice(0,12);
 res.innerHTML=hits.map(x=>`<li><a href="${{x.u}}">${{esc(x.t)}}${{x.v?` <em>${{esc(x.v)}}</em>`:''}}</a></li>`).join('')||'<li class="nohit">No match — try a different word from your report.</li>';
 res.hidden=false;
}});
</script>'''
    return head(title, desc, canonical, "website", nodes) + header_html() + \
        f'<main id="main" class="wrap">{main}</main>' + footer_html()

# ---------- sitemaps ----------
def build_sitemaps(all_urls):
    def urlset(entries):
        rows = "\n".join(
            f'<url><loc>{u}</loc><lastmod>{MODIFIED}</lastmod><changefreq>{cf}</changefreq><priority>{pr}</priority></url>'
            for u, cf, pr in entries)
        return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'
    open(os.path.join(OUT, "sitemap.xml"), "w").write(urlset(all_urls))

# ---------- MAIN ----------
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    all_urls = [(HOST + "/", "weekly", "1.0")]
    write_page("", render_home())
    for s in HUB_SLUGS:
        write_page(s, render_hub(s))
        all_urls.append((f"{HOST}/{s}/", "weekly", "0.8"))
    for s in content_slugs:
        write_page(s, render_content(s))
        all_urls.append((f"{HOST}/{s}/", "monthly", "0.9"))
    for s in POLICY:
        write_page(s, render_policy(s))
        all_urls.append((f"{HOST}/{s}/", "yearly", "0.3"))

    build_sitemaps(all_urls)
    write_support_files()
    print(f"Built {len(all_urls)} pages into {OUT}")

def write_support_files():
    # robots.txt — AI-crawler friendly
    ai_bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-Web", "anthropic-ai",
               "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended",
               "Bingbot", "CCBot", "Amazonbot", "Bytespider", "Meta-ExternalAgent", "cohere-ai"]
    bot_block = "\n".join(f"User-agent: {b}\nAllow: /\n" for b in ai_bots)
    robots = (f"# {SITE}\nUser-agent: *\nAllow: /\n\n"
              f"# AI / answer-engine crawlers — explicitly welcome\n{bot_block}\n"
              f"Sitemap: {HOST}/sitemap.xml\n")
    open(os.path.join(OUT, "robots.txt"), "w").write(robots)

    # .htaccess
    htaccess = f'''# {SITE} — Apache config for Cloudways
DirectoryIndex index.html index.htm index.php

RewriteEngine On
# Force HTTPS
RewriteCond %{{HTTPS}} !=on
RewriteCond %{{HTTP:X-Forwarded-Proto}} !=https
RewriteRule ^ https://%{{HTTP_HOST}}%{{REQUEST_URI}} [L,R=301]
# Force www (canonical)
RewriteCond %{{HTTP_HOST}} ^ecgmeans\\.com [NC]
RewriteRule ^ https://www.ecgmeans.com%{{REQUEST_URI}} [L,R=301]
# Strip index.html
RewriteCond %{{THE_REQUEST}} \\s/(.*/)?index\\.html[\\s?] [NC]
RewriteRule ^(.*/)?index\\.html$ /%1 [R=301,L]
# Block source dirs if ever present
RewriteRule ^(content|scripts|src|node_modules|\\.github|\\.git)(/|$) - [F,L]

ErrorDocument 404 /404.html

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"
</IfModule>
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType text/html "access plus 2 hours"
  ExpiresByType application/xml "access plus 1 day"
</IfModule>
<IfModule mod_headers.c>
  <FilesMatch "\\.(css|svg|png|ico|woff2)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
  <FilesMatch "\\.html$">
    Header set Cache-Control "public, max-age=7200, must-revalidate"
  </FilesMatch>
</IfModule>
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/xml text/plain image/svg+xml application/json
</IfModule>
'''
    open(os.path.join(OUT, ".htaccess"), "w").write(htaccess)

    # index.php shim
    php = '''<?php
// Static build. Serve homepage for root, real 404 otherwise.
$path = rtrim(parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/', '/');
if ($path === '' || $path === '/index' || $path === '/index.php' || $path === '/index.html') {
    header('Content-Type: text/html; charset=utf-8');
    readfile(__DIR__ . '/index.html');
    exit;
}
http_response_code(404);
header('Content-Type: text/html; charset=utf-8');
readfile(__DIR__ . '/404.html');
'''
    open(os.path.join(OUT, "index.php"), "w").write(php)

    # 404
    nf = head("Page not found — ECG Means", "That page could not be found.", HOST + "/404.html", "website", []) \
        + header_html() + ('<main id="main" class="wrap narrow"><article><h1>Page not found</h1>'
        '<p class="lede">That page could not be found. Try searching for your ECG phrase from the home page.</p>'
        '<p><a class="btn" href="/">Go to the ECG Means home page</a></p></article></main>') + footer_html()
    open(os.path.join(OUT, "404.html"), "w").write(nf)

    # README + package.json + gitignore
    open(os.path.join(OUT, ".gitignore"), "w").write("node_modules/\n.DS_Store\n*.log\n")

    # favicon
    open(os.path.join(OUT, "favicon.svg"), "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#b91c1c"/><path d="M6 36h12l6-16 8 30 8-22 4 8h14" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/></svg>')

    build_llms()

def build_llms():
    # llms.txt (concise) and llms-full.txt (with page summaries)
    lines = [f"# {SITE}", "",
             f"> Independent, clinician-reviewed plain-English explanations of the phrases printed on ECG/EKG reports. "
             f"Every page is written and reviewed by {REVIEWER}, {REVIEWER_SUFFIX} ({PMDC}) and states plainly whether a finding is usually harmless, context-dependent, needs clinician review, or warrants prompt care. Educational only; not a substitute for the clinician who ordered the test.", ""]
    for h in HUB_SLUGS:
        lines.append(f"## {HUB_LABEL[h]}")
        lines.append(f"- [{pages[h].get('H1', h)}]({HOST}/{h}/): {pages[h].get('DESC','')}")
        for m in hub_members[h]:
            lines.append(f"- [{pages[m].get('H1', m)}]({HOST}/{m}/): {pages[m].get('DESC','')}")
        lines.append("")
    lines.append("## About")
    for s in POLICY:
        lines.append(f"- [{pages[s].get('H1', s)}]({HOST}/{s}/): {pages[s].get('DESC','')}")
    open(os.path.join(OUT, "llms.txt"), "w").write("\n".join(lines) + "\n")

    # llms-full.txt: include lede + quick answer for each content page
    full = [f"# {SITE} — full content index", "",
            f"> {TAGLINE}. Reviewed by {REVIEWER}, {REVIEWER_SUFFIX} ({PMDC}).", ""]
    for h in HUB_SLUGS:
        full.append(f"## {HUB_LABEL[h]}")
        full.append("")
        for m in hub_members[h]:
            f = pages[m]
            full.append(f"### {f.get('H1', m)}")
            full.append(f"URL: {HOST}/{m}/")
            q = f.get("QUICK", "").strip()
            if q and q.upper() != "NONE":
                full.append(f"Verdict/quick answer: {q}")
            full.append(f.get("LEDE", "").strip())
            full.append("")
    open(os.path.join(OUT, "llms-full.txt"), "w").write("\n".join(full) + "\n")

if __name__ == "__main__":
    main()
