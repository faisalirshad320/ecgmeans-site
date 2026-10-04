#!/usr/bin/env python3
# Generates CSS + image assets into site/assets/ (run AFTER build.py)
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
CSS_DIR = os.path.join(OUT, "assets", "css")
IMG_DIR = os.path.join(OUT, "assets", "img")
os.makedirs(CSS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

BRAND = (185, 28, 28)   # #b91c1c

CSS = r""":root{
  --brand:#b91c1c; --brand-d:#991b1b; --ink:#1a1a1a; --muted:#595f6b; --line:#e6e8ec;
  --bg:#ffffff; --soft:#f7f8fa; --soft2:#eef1f5; --max:1080px; --rad:12px;
  --ok:#15803d; --ok-bg:#eafaf0; --warn:#b45309; --warn-bg:#fff6e8;
  --review:#c2410c; --review-bg:#fff1e9; --urgent:#b91c1c; --urgent-bg:#fdecec;
  --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#e9ebee; --muted:#a2a9b4; --line:#2a2e35; --bg:#14161a; --soft:#1b1e24; --soft2:#20242b;
  --ok-bg:#122a1c; --warn-bg:#2a2210; --review-bg:#2a1a12; --urgent-bg:#2a1414;
}}
:root[data-theme="dark"]{
  --ink:#e9ebee; --muted:#a2a9b4; --line:#2a2e35; --bg:#14161a; --soft:#1b1e24; --soft2:#20242b;
  --ok-bg:#122a1c; --warn-bg:#2a2210; --review-bg:#2a1a12; --urgent-bg:#2a1414;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font);
  font-size:18px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:var(--max);margin:0 auto;padding:0 20px}
.narrow{max-width:760px}
a{color:var(--brand-d);text-underline-offset:2px}
a:hover{color:var(--brand)}
img{max-width:100%;height:auto}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:50}
h1{font-size:2rem;line-height:1.2;margin:.2em 0 .3em;letter-spacing:-.01em}
h2{font-size:1.4rem;line-height:1.25;margin:1.8em 0 .5em}
h3{font-size:1.12rem;margin:1.4em 0 .3em}
p{margin:.7em 0}
/* header */
.site-head{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:saturate(1.3) blur(8px);border-bottom:1px solid var(--line)}
.site-head .wrap{display:flex;align-items:center;gap:14px;height:62px}
.brand{display:flex;align-items:center;gap:9px;font-weight:800;color:var(--ink);text-decoration:none;font-size:1.12rem}
.brand .mark{border-radius:8px;flex:none}
.nav{margin-left:auto;display:flex;gap:4px;flex-wrap:wrap}
.nav a{color:var(--muted);text-decoration:none;font-weight:600;font-size:.95rem;padding:8px 10px;border-radius:8px}
.nav a:hover{color:var(--ink);background:var(--soft2)}
.menu-btn{display:none;margin-left:auto;background:var(--soft2);border:1px solid var(--line);
  border-radius:8px;font-size:1.2rem;line-height:1;padding:8px 12px;color:var(--ink);cursor:pointer}
@media(max-width:820px){
  .menu-btn{display:block}
  .nav{display:none;position:absolute;top:62px;left:0;right:0;background:var(--bg);
    border-bottom:1px solid var(--line);flex-direction:column;padding:10px 16px;gap:2px}
  .nav.open{display:flex}
  .nav a{padding:12px 10px;font-size:1.05rem}
}
main{padding:24px 0 48px}
/* breadcrumbs */
.crumbs{font-size:.85rem;color:var(--muted);margin:.2em 0 1em;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:var(--brand)}
.crumbs .sep{opacity:.5}
.lede{font-size:1.18rem;color:var(--ink);margin:.4em 0 1em}
/* verdict badges */
.verdict-row{margin:.2em 0 .8em}
.verdict{display:inline-block;font-size:.8rem;font-weight:700;padding:5px 12px;border-radius:999px;letter-spacing:.01em}
.verdict-ok{color:var(--ok);background:var(--ok-bg)}
.verdict-warn{color:var(--warn);background:var(--warn-bg)}
.verdict-review{color:var(--review);background:var(--review-bg)}
.verdict-urgent{color:var(--urgent);background:var(--urgent-bg)}
/* byline */
.byline{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center;font-size:.85rem;color:var(--muted);
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:10px 0;margin:0 0 1.2em}
.byline .rev strong{color:var(--ink)}
/* answer callout */
.answer{background:var(--soft);border:1px solid var(--line);border-left:4px solid var(--brand);
  border-radius:var(--rad);padding:14px 18px;margin:1.2em 0}
.answer-k{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--brand);margin-bottom:4px}
.answer p{margin:0}
/* callouts */
.callout{border-radius:var(--rad);padding:12px 16px;margin:1.1em 0;border:1px solid var(--line)}
.callout-urgent{background:var(--urgent-bg);border-color:#f3c2c2;color:var(--ink)}
/* toc */
.toc{background:var(--soft);border:1px solid var(--line);border-radius:var(--rad);padding:12px 18px;margin:1.3em 0}
.toc-k{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:6px}
.toc ol{margin:0;padding-left:1.2em}
.toc a{text-decoration:none}.toc a:hover{text-decoration:underline}
/* body */
.body h2{scroll-margin-top:76px}
.body ul,.body ol{padding-left:1.3em}
.body li{margin:.3em 0}
.body table{width:100%;border-collapse:collapse;margin:1.1em 0;font-size:.95rem;display:block;overflow-x:auto}
.body th,.body td{border:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
.body thead th{background:var(--soft2)}
.body caption{caption-side:bottom;color:var(--muted);font-size:.82rem;margin-top:6px;text-align:left}
/* faq */
.faq{margin-top:2em;border-top:1px solid var(--line);padding-top:.4em}
.faq-item{border-bottom:1px solid var(--line);padding:.6em 0}
.faq-item h3{margin:.2em 0}
.faq-item p{margin:.2em 0;color:var(--muted)}
.also{font-size:.85rem;color:var(--muted);margin-top:1.4em}
.also span{font-weight:700}
/* related + cards */
.related,.sources,.other-hubs,.hubs-section,.az,.how{margin-top:2em}
.cards{list-style:none;padding:0;margin:.6em 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.card a{display:flex;justify-content:space-between;align-items:center;gap:8px;background:var(--soft);
  border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink);height:100%}
.card a:hover{border-color:var(--brand);background:var(--soft2)}
.card-t{font-weight:600;font-size:.96rem;line-height:1.3}
.rel-list{list-style:none;padding:0;margin:.6em 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}
.rel-list li{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.rel-list a{font-weight:600;text-decoration:none;display:block}
.rel-note{display:block;font-size:.78rem;color:var(--muted);margin-top:2px}
.sources ol{padding-left:1.2em;color:var(--muted);font-size:.92rem}
.sources a{color:var(--muted)}
/* hero + search */
.hero{text-align:center;padding:26px 0 8px}
.hero .lede{max-width:640px;margin:.4em auto 1.2em}
.search{max-width:640px;margin:0 auto;position:relative}
.search input{width:100%;font-size:1.1rem;padding:15px 18px;border:2px solid var(--line);border-radius:14px;
  background:var(--bg);color:var(--ink)}
.search input:focus{outline:none;border-color:var(--brand)}
.results{list-style:none;margin:6px 0 0;padding:6px;position:absolute;left:0;right:0;z-index:20;
  background:var(--bg);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.12);text-align:left}
.results li a{display:flex;justify-content:space-between;gap:8px;padding:10px 12px;border-radius:8px;text-decoration:none;color:var(--ink)}
.results li a:hover{background:var(--soft2)}
.results em{color:var(--muted);font-style:normal;font-size:.82rem}
.results .nohit{padding:10px 12px;color:var(--muted)}
/* hub cards */
.hubcards{list-style:none;padding:0;margin:1em 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.hubcard a{display:block;background:var(--soft);border:1px solid var(--line);border-radius:14px;padding:18px;text-decoration:none;color:var(--ink);height:100%}
.hubcard a:hover{border-color:var(--brand)}
.hc-t{display:block;font-weight:800;font-size:1.08rem}
.hc-d{display:block;color:var(--muted);font-size:.9rem;margin:6px 0}
.hc-n{display:inline-block;font-size:.72rem;font-weight:700;color:var(--brand);background:var(--urgent-bg);padding:3px 9px;border-radius:999px}
.btn{display:inline-block;background:var(--brand);color:#fff;text-decoration:none;font-weight:700;padding:12px 20px;border-radius:10px}
.btn:hover{background:var(--brand-d);color:#fff}
.ad{margin:1.4em 0;min-height:0}
/* footer */
.site-foot{border-top:1px solid var(--line);background:var(--soft);margin-top:40px;padding:30px 0;font-size:.9rem;color:var(--muted)}
.foot-brand strong{color:var(--ink)}
.foot-links{display:flex;flex-wrap:wrap;gap:8px 18px;margin:12px 0}
.foot-links a{color:var(--muted);text-decoration:none}.foot-links a:hover{color:var(--brand)}
.foot-note{font-size:.82rem;opacity:.9}
.copyright{font-size:.8rem}
.ecg-fig{margin:1.2em 0 1.4em;background:#fff8f8;border:1px solid var(--line);border-radius:var(--rad);padding:8px}
.ecg-fig img{display:block;width:100%;height:auto;border-radius:6px}
.ecg-fig figcaption{font-size:.82rem;color:var(--muted);margin-top:6px;line-height:1.45}
.hub-intro{margin:2em 0 1em;max-width:760px}
.tool{border:2px solid var(--brand);border-radius:var(--rad);padding:18px;margin:1.2em 0 1.4em;background:var(--soft)}
.tool-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.tool label{display:flex;flex-direction:column;gap:6px;font-weight:700;font-size:.9rem}
.tool input,.tool select{font:inherit;font-size:1rem;padding:10px 12px;border:1px solid #c9ced6;border-radius:8px;background:var(--bg);color:var(--ink);min-width:0}
.tool input:focus,.tool select:focus{outline:2px solid var(--brand);outline-offset:1px}
.tool-out{margin-top:14px}
.tool-hint,.tool-note{color:var(--muted);font-size:.88rem;margin:.4em 0}
.tool-res{margin:.3em 0}
.tool-big{font-size:2rem;font-weight:800;color:var(--ink)}
.tool-how{color:var(--muted);font-size:.9rem}
.tool-table{width:100%;border-collapse:collapse;margin:.6em 0;font-size:.92rem}
.tool-table th,.tool-table td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:middle}
@media (max-width:560px){.tool-table td:nth-child(2),.tool-table th:nth-child(2){display:none}}
@media(max-width:520px){ body{font-size:17px} h1{font-size:1.6rem} .hero{padding:12px 0} }
"""
open(os.path.join(CSS_DIR, "style.css"), "w").write(CSS)

# ---- fonts ----
def load_font(sz, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def ecg_wave(draw, x0, y0, w, h, color, width):
    # draw a stylised ECG trace across width w centered at y0, amplitude ~h
    pts = []
    import math
    n = 240
    for i in range(n):
        t = i / n
        x = x0 + t * w
        # baseline with a QRS spike repeating
        phase = (t * 3.0) % 1.0
        y = y0
        if 0.42 < phase < 0.46: y = y0 - h*0.15      # P
        elif 0.50 <= phase < 0.52: y = y0 + h*0.15   # Q
        elif 0.52 <= phase < 0.55: y = y0 - h         # R
        elif 0.55 <= phase < 0.58: y = y0 + h*0.45    # S
        elif 0.63 < phase < 0.70: y = y0 - h*0.25     # T
        pts.append((x, y))
    draw.line(pts, fill=color, width=width, joint="curve")

def rounded_icon(size):
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    d = ImageDraw.Draw(img)
    r = int(size*0.19)
    d.rounded_rectangle([0,0,size-1,size-1], radius=r, fill=BRAND)
    # waveform
    m = int(size*0.12)
    ecg_wave(d, m, size*0.56, size-2*m, size*0.26, (255,255,255,255), max(2,int(size*0.06)))
    return img

# apple touch icon 180 + 512 logo
rounded_icon(180).save(os.path.join(IMG_DIR, "icon-180.png"))
rounded_icon(512).save(os.path.join(IMG_DIR, "logo.png"))

# OG image 1200x630
W,H = 1200,630
og = Image.new("RGB",(W,H),(255,255,255))
d = ImageDraw.Draw(og)
# left red panel
d.rectangle([0,0,W,H], fill=(255,255,255))
d.rectangle([0,H-14,W,H], fill=BRAND)
# icon
ic = rounded_icon(132)
og.paste(ic,(80,70),ic)
# wordmark
d.text((230,92), "ECG Means", font=load_font(66,True), fill=(26,26,26))
d.text((232,172), "Your ECG report, explained in plain English", font=load_font(30,False), fill=(89,95,107))
# big headline
d.text((80,300), "What does that line on", font=load_font(62,True), fill=(26,26,26))
d.text((80,372), "your ECG report mean?", font=load_font(62,True), fill=BRAND)
# ecg trace accent
ecg_wave(d, 80, 520, W-160, 60, BRAND, 6)
d.text((80,560), "Reviewed by Dr. Faisal Irshad, MBBS · PMDC 54440-S", font=load_font(26,False), fill=(89,95,107))
og.save(os.path.join(IMG_DIR, "og-default.png"), "PNG")
print("assets written:", os.listdir(IMG_DIR), "+ css")
