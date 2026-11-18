#!/usr/bin/env python3
"""Static site generator for prodigalman.com (Tim Couet, Prodigal Man).

Rebuilds every page of the original site with the same URL structure
(/book/, /podcast/, /socials/, /blog/, /blog/<slug>/, /speaking/, /more/about/,
/more/bio/, /more/contact/, /more/consulting/) in the look of foreverchanged.vercel.app.

Usage:  python3 build.py            -> writes site/ with folder-style links (book/)
        python3 build.py --file     -> writes site/ with explicit links (book/index.html),
                                       for previews that cannot serve directory indexes.
No dependencies beyond the standard library.
"""
import json, os, sys, html, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
CONTENT = os.path.join(ROOT, "content")
FILE_LINKS = "--file" in sys.argv
BASE_URL = os.environ.get("SITE_BASE", "https://prodigalman.com/")  # canonical + og:image host; set SITE_BASE=https://prodigalman.vercel.app/ until the domain moves

YT_CHANNEL = "https://www.youtube.com/channel/UCoHdydcWIomHBo41xX4gWcg"
INSTAGRAM = "https://www.instagram.com/prodigalman/"
FACEBOOK = "https://www.facebook.com/ProdigalManMinistries/"
AMAZON = "https://a.co/d/09KZT5xQ"
# Contact form delivery: FormSubmit emails each submission to Tim. The first live submission
# sends Tim an activation email he must click once. After activation FormSubmit also offers a
# random alias string that can replace the address here so it is not visible in the HTML.
FORM_ENDPOINT = "https://formsubmit.co/prodigalmanministries@gmail.com"

NAV = [
    ("", "Home"),
    ("book/", "Book"),
    ("podcast/", "Podcast"),
    ("socials/", "Socials"),
    ("blog/", "Blog"),
    ("speaking/", "Speaking"),
    ("more/about/", "About"),
    ("more/bio/", "Bio"),
    ("more/consulting/", "Consulting"),
    ("more/contact/", "Contact"),
]

posts = json.load(open(os.path.join(CONTENT, "posts.json"), encoding="utf-8"))

# ---------------------------------------------------------------- helpers

def esc(s):
    return html.escape(s, quote=True)


def href(path, depth):
    """Link to a site path ('book/', '', 'blog/slug/') from a page `depth` folders deep."""
    rel = "../" * depth
    if FILE_LINKS:
        if path == "" or path.endswith("/"):
            path = path + "index.html"
    out = rel + path
    return out if out else "./"


def asset(path, depth):
    return "../" * depth + "assets/" + path


def yt_thumb(vid, depth):
    return asset(f"img/yt-{vid}.jpg", depth)


def para_html(paragraphs):
    out = []
    for p in paragraphs:
        # scripture references on their own line become a cite under the quote
        if p.isupper() and len(p) < 80:
            out.append(f"<p class=\"shout\">{esc(p)}</p>")
        elif p.startswith('"') and p.endswith('"') and len(p) < 400:
            out.append(f"<blockquote><p>{esc(p.strip(chr(34)))}</p></blockquote>")
        elif re.match(r'^(Genesis|Exodus|Matthew|John|Luke|Romans|2 Corinthians|Proverbs|Ephesians)\s+\d', p) and len(p) < 40:
            out.append(f"<p class=\"ref\">{esc(p)}</p>")
        else:
            out.append(f"<p>{esc(p)}</p>")
    return "\n".join(out)


def excerpt(paragraphs, n=160):
    t = paragraphs[0]
    if len(t) < 60 and len(paragraphs) > 1:
        t = paragraphs[1]
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > n:
        t = t[: n].rsplit(" ", 1)[0] + "..."
    return t


# ---------------------------------------------------------------- CSS

CSS = r"""
:root{
  --ink:#121010; --ink-2:#1a1615; --ink-3:#242020; --ink-line:rgba(255,255,255,.1);
  --paper:#f6f3ef; --paper-2:#ede8e1; --paper-line:rgba(30,22,18,.12);
  --text:#1c1715; --muted:#6b625c; --on-ink:#f5f0ea; --on-ink-muted:#b3a89f;
  --copper:#c2641f; --copper-deep:#8f4712; --copper-soft:#f7e6d6; --copper-glow:#e9a567;
  --gold:#d2a64c;
  --display:"Fraunces", Georgia, "Times New Roman", serif;
  --body:"Hanken Grotesk", "Helvetica Neue", Arial, sans-serif;
  --max:1180px; --gutter:clamp(18px,4vw,48px); --radius:6px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{animation:none!important;transition:none!important}}
body{margin:0;background:var(--paper);color:var(--text);font-family:var(--body);font-size:17px;line-height:1.6}
img{max-width:100%;height:auto;display:block}
a{color:inherit}
h1,h2,h3,h4{font-family:var(--display);font-weight:500;line-height:1.08;margin:0;text-wrap:balance;letter-spacing:-.01em}
h1{font-size:clamp(2.4rem,5.2vw,4.4rem);font-variation-settings:"opsz" 144,"SOFT" 30}
h2{font-size:clamp(1.9rem,3.6vw,3rem);font-variation-settings:"opsz" 96}
h3{font-size:clamp(1.3rem,2vw,1.6rem)}
h4{font-size:1.15rem}
p{margin:0}
.wrap{max-width:var(--max);margin-inline:auto;padding-inline:var(--gutter)}
.narrow{max-width:760px}
.eyebrow{font-size:.78rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--copper)}
.ink .eyebrow,.ink-2 .eyebrow{color:var(--copper-glow)}
.lede{font-size:1.2rem;line-height:1.55;color:var(--muted);max-width:60ch}
.ink .lede,.ink-2 .lede{color:var(--on-ink-muted)}
.muted{color:var(--muted)}
.ink .muted{color:var(--on-ink-muted)}
.prose{max-width:68ch;font-size:1.08rem}
.prose p+p{margin-top:1.1em}
.prose a{color:var(--copper);text-decoration-thickness:1px;text-underline-offset:3px}
.prose blockquote{margin:1.8em 0;padding-left:1.15em;border-left:2px solid var(--copper-glow);font-family:var(--display);font-style:italic;font-size:1.12em;line-height:1.5}
.prose blockquote p{margin:0}
.prose .ref{margin-top:.5em;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;color:var(--copper)}
.prose .shout{margin:1.6em 0;font-family:var(--display);font-size:1.5em;line-height:1.2;color:var(--copper-deep);text-transform:none}
.prose h3{margin:1.8em 0 .5em}

section{padding-block:clamp(56px,8vw,112px)}
.ink{background:var(--ink);color:var(--on-ink)}
.ink-2{background:var(--ink-2);color:var(--on-ink)}
.paper-2{background:var(--paper-2)}
.section-head{display:grid;grid-template-columns:1fr auto;gap:1.5rem 3rem;align-items:end;margin-bottom:clamp(28px,4vw,48px)}
.section-head .lede{margin-top:.75rem}
.section-head h2{margin-top:.5rem}
@media (max-width:720px){.section-head{grid-template-columns:1fr}}

.btn{display:inline-flex;align-items:center;gap:.6rem;padding:.85rem 1.4rem;border-radius:999px;font-weight:600;font-size:.95rem;text-decoration:none;border:1.5px solid transparent;transition:transform .15s ease,background .15s ease,border-color .15s ease;cursor:pointer;font-family:var(--body);line-height:1}
.btn:hover{transform:translateY(-1px)}
.btn:focus-visible,a:focus-visible,button:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid var(--copper-glow);outline-offset:3px}
.btn-primary{background:var(--copper);color:#fff}
.btn-primary:hover{background:var(--copper-deep)}
.btn-ghost{border-color:var(--paper-line);color:var(--text);background:transparent}
.btn-ghost:hover{border-color:var(--text)}
.ink .btn-ghost,.ink-2 .btn-ghost,.hero .btn-ghost,.stage-band .btn-ghost,.cta-band .btn-ghost{border-color:rgba(255,255,255,.28);color:var(--on-ink)}
.ink .btn-ghost:hover,.ink-2 .btn-ghost:hover,.hero .btn-ghost:hover,.stage-band .btn-ghost:hover,.cta-band .btn-ghost:hover{border-color:#fff}
.btn-light{background:#fff;color:var(--ink)}
.btn svg,.link svg{width:1em;height:1em;flex:none}
.btn-row{display:flex;flex-wrap:wrap;gap:.75rem;align-items:center}
.link{color:var(--copper);font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:.35rem}
.link:hover{text-decoration:underline;text-underline-offset:3px}
.ink .link,.ink-2 .link{color:var(--copper-glow)}

/* header */
.site-header{position:sticky;top:0;z-index:50;background:#000;border-bottom:1px solid var(--ink-line);color:var(--on-ink)}
.site-header .wrap{display:flex;align-items:center;justify-content:space-between;gap:1.5rem;min-height:72px}
.brand{display:flex;align-items:center;gap:.75rem;text-decoration:none;color:inherit}
.brand img{height:42px;width:42px;border-radius:50%}
.brand span{font-family:var(--display);font-size:1.15rem;letter-spacing:.01em;white-space:nowrap;color:#fff}
.nav{display:flex;align-items:center;gap:clamp(.8rem,1.6vw,1.4rem)}
.nav a{text-decoration:none;font-size:.92rem;font-weight:500;color:var(--on-ink-muted);padding:.4rem 0;border-bottom:1.5px solid transparent;transition:color .15s}
.nav a:hover,.nav a[aria-current]{color:#fff}
.nav a[aria-current]{border-bottom-color:var(--copper-glow)}
.nav .btn{padding:.6rem 1.1rem;font-size:.88rem;color:#fff;border-bottom:0}
.nav-toggle{display:none;background:none;border:1.5px solid rgba(255,255,255,.25);color:#fff;border-radius:6px;padding:.45rem .6rem;font:inherit;font-size:.85rem;cursor:pointer}
@media (max-width:1040px){
  .nav-toggle{display:inline-flex;align-items:center;gap:.5rem}
  .nav{display:none;position:absolute;left:0;right:0;top:100%;background:#000;flex-direction:column;align-items:stretch;padding:1rem var(--gutter) 1.5rem;gap:.25rem;border-bottom:1px solid var(--ink-line)}
  .nav.is-open{display:flex}
  .nav a{padding:.7rem 0;font-size:1.05rem;border-bottom:1px solid var(--ink-line)}
  .nav .btn{margin-top:.75rem;justify-content:center}
}

/* hero */
.hero{position:relative;overflow:hidden;padding-block:clamp(56px,9vw,120px) clamp(48px,7vw,96px);background:var(--ink);color:var(--on-ink)}
.hero::before{content:"";position:absolute;inset:0;background:center/cover no-repeat;opacity:.45}
.hero::after{content:"";position:absolute;inset:0;background:radial-gradient(60% 70% at 70% 30%,rgba(194,100,31,.30),transparent 70%),linear-gradient(180deg,rgba(18,16,16,.3),var(--ink) 95%)}
.hero .wrap{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(280px,.85fr);gap:clamp(2rem,5vw,5rem);align-items:center}
.hero h1{margin:1rem 0 1.25rem}
.hero h1 em{font-style:italic;font-weight:400;color:var(--copper-glow)}
.hero .lede{max-width:52ch}
.hero .btn-row{margin-top:2rem}
.hero-roles{margin-top:2.25rem;display:flex;flex-wrap:wrap;gap:.5rem .9rem;color:var(--on-ink-muted);font-size:.85rem;letter-spacing:.1em;text-transform:uppercase}
.hero-roles span+span::before{content:"\00b7";margin-right:.9rem;color:var(--copper-glow)}
.poster{position:relative;justify-self:center;max-width:380px;transform:rotate(1.5deg);transition:transform .4s ease;margin:0}
.poster:hover{transform:rotate(0) scale(1.01)}
.poster img{border-radius:8px;box-shadow:0 40px 80px -20px rgba(0,0,0,.75),0 0 0 1px rgba(255,255,255,.08)}
.poster figcaption{margin-top:1rem;text-align:center;font-size:.82rem;color:var(--on-ink-muted);letter-spacing:.04em}
.poster figcaption b{color:var(--gold);font-weight:600}
@media (max-width:860px){.hero .wrap{grid-template-columns:1fr}.poster{transform:none;max-width:320px;justify-self:start}}

/* interior page hero */
.page-hero{background:var(--ink);color:var(--on-ink);padding-block:clamp(44px,6vw,80px);position:relative;overflow:hidden}
.page-hero::before{content:"";position:absolute;inset:0;background:center/cover no-repeat;opacity:.28}
.page-hero::after{content:"";position:absolute;inset:0;background:radial-gradient(50% 80% at 85% 20%,rgba(194,100,31,.28),transparent 70%),linear-gradient(180deg,rgba(18,16,16,.35),var(--ink));pointer-events:none}
.page-hero .wrap{position:relative;z-index:1}
.page-hero h1{margin-top:.75rem}
.page-hero .lede{margin-top:1rem}
.crumbs{font-size:.85rem;color:var(--on-ink-muted);display:flex;gap:.5rem;flex-wrap:wrap}
.crumbs a{color:inherit;text-decoration:none}
.crumbs a:hover{color:#fff}

/* grids and cards */
.grid{display:grid;gap:1.5rem}
.grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
@media (max-width:980px){.grid-3{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:620px){.grid-2,.grid-3{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--paper-line);border-radius:var(--radius);padding:1.6rem;display:flex;flex-direction:column;gap:.75rem}
.ink .card,.ink-2 .card{background:var(--ink-3);border-color:var(--ink-line)}
.card h3{font-size:1.3rem}
.card .link{margin-top:auto}
.card .pill{align-self:flex-start}
.pill{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:.3rem .6rem;border-radius:4px;background:var(--copper-soft);color:var(--copper-deep)}
.ink .pill,.ink-2 .pill{background:rgba(233,165,103,.16);color:var(--copper-glow)}

/* feature tiles (Connect) */
.tile{display:flex;flex-direction:column;background:var(--ink-3);border:1px solid var(--ink-line);border-radius:var(--radius);overflow:hidden;text-decoration:none;color:inherit;transition:transform .2s,border-color .2s}
.tile:hover{transform:translateY(-3px);border-color:rgba(255,255,255,.3)}
.tile img{aspect-ratio:4/3;width:100%;object-fit:cover}
.tile-body{padding:1.2rem 1.3rem 1.4rem;display:flex;flex-direction:column;gap:.4rem}
.tile-body h3{font-size:1.25rem}
.tile-body p{color:var(--on-ink-muted);font-size:.95rem}
.tile-body .link{margin-top:.5rem}

/* video facade */
.video{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;border-radius:var(--radius);background:#000;text-decoration:none;color:#fff}
.video img{width:100%;height:100%;object-fit:cover;opacity:.92;transition:transform .5s ease,opacity .3s}
.video:hover img{transform:scale(1.03);opacity:1}
.video .play{position:absolute;inset:0;display:grid;place-items:center}
.video .play::before{content:"";width:68px;height:68px;border-radius:50%;background:rgba(18,16,16,.72);border:1.5px solid rgba(255,255,255,.5);backdrop-filter:blur(6px);transition:background .2s,transform .2s}
.video .play::after{content:"";position:absolute;width:0;height:0;border-left:20px solid #fff;border-top:12px solid transparent;border-bottom:12px solid transparent;margin-left:5px}
.video:hover .play::before{background:var(--copper);transform:scale(1.06)}
.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.talk{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:clamp(1.5rem,4vw,3.5rem);align-items:center}
.talk+.talk{margin-top:clamp(2.5rem,5vw,4rem);padding-top:clamp(2.5rem,5vw,4rem);border-top:1px solid var(--paper-line)}
.talk h3{font-size:clamp(1.5rem,2.6vw,2.1rem);margin:.6rem 0 .8rem}
@media (max-width:820px){.talk{grid-template-columns:1fr}}

/* split layouts */
.split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(2rem,5vw,5rem);align-items:center}
@media (max-width:860px){.split{grid-template-columns:1fr}}
.split img{border-radius:var(--radius)}
.roles{list-style:none;margin:1.5rem 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem 1.5rem}
.roles li{display:flex;align-items:center;gap:.6rem;font-weight:500}
.roles li::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--copper);flex:none}
.tagline{font-family:var(--display);font-size:clamp(1.5rem,3vw,2.3rem);line-height:1.2;color:var(--ink)}
.tagline b{color:var(--copper);font-weight:500}
.logo-round,.split img.logo-round{width:150px;height:150px;border-radius:50%;box-shadow:none;filter:drop-shadow(0 18px 24px rgba(0,0,0,.38))}

/* book */
.book-cover{max-width:420px;justify-self:center;margin:0;position:relative;padding-bottom:36px}
.book-cover img{position:relative;z-index:1;filter:drop-shadow(0 28px 30px rgba(0,0,0,.42)) drop-shadow(0 8px 10px rgba(0,0,0,.28)) drop-shadow(0 1px 2px rgba(0,0,0,.35))}
.book-cover::after{content:"";position:absolute;left:6%;right:6%;bottom:2px;height:56px;border-radius:50%;background:radial-gradient(ellipse at center,rgba(0,0,0,.45),rgba(0,0,0,.18) 45%,transparent 72%);filter:blur(6px)}

/* podcast */
.show{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:clamp(1.5rem,4vw,3.5rem);align-items:center}
.show+.show{margin-top:clamp(2.5rem,5vw,4rem);padding-top:clamp(2.5rem,5vw,4rem);border-top:1px solid var(--ink-line)}
.show img{border-radius:var(--radius);box-shadow:0 30px 60px -20px rgba(0,0,0,.7)}
.show h3{font-size:clamp(1.6rem,2.8vw,2.3rem);margin:.6rem 0 .8rem}
@media (max-width:720px){.show{grid-template-columns:1fr}.show img{max-width:360px}}

/* social cards */
.social-card{display:flex;flex-direction:column;gap:.75rem;background:#fff;border:1px solid var(--paper-line);border-radius:var(--radius);padding:1.6rem;text-decoration:none;color:inherit;transition:transform .2s,border-color .2s}
.social-card:hover{transform:translateY(-3px);border-color:var(--copper)}
.social-card .ico{width:44px;height:44px;border-radius:50%;background:var(--copper-soft);display:grid;place-items:center;color:var(--copper-deep)}
.social-card .ico svg{width:22px;height:22px;fill:currentColor}
.social-card h3{font-size:1.25rem}
.social-card p{color:var(--muted);font-size:.95rem}
.social-card .link{margin-top:auto}

/* blog */
.post-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.5rem}
@media (max-width:980px){.post-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:620px){.post-grid{grid-template-columns:1fr}}
.post-card{display:flex;flex-direction:column;gap:.6rem;background:#fff;border:1px solid var(--paper-line);border-radius:var(--radius);padding:1.6rem;text-decoration:none;color:inherit;transition:transform .2s,border-color .2s}
.post-card:hover{transform:translateY(-3px);border-color:var(--copper)}
.post-card .num{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;color:var(--copper);font-weight:600}
.post-card h3{font-size:1.35rem}
.post-card p{color:var(--muted);font-size:.95rem}
.post-card .link{margin-top:auto}
.post-feature{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(1.5rem,4vw,3.5rem);align-items:center;margin-bottom:clamp(2.5rem,5vw,4rem)}
.post-feature img{border-radius:var(--radius);aspect-ratio:4/3;object-fit:cover;width:100%}
.post-feature h2{margin:.6rem 0 1rem}
@media (max-width:820px){.post-feature{grid-template-columns:1fr}}
.post-head{max-width:68ch}
.post-nav{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:clamp(2.5rem,5vw,4rem);padding-top:2rem;border-top:1px solid var(--paper-line)}
.post-nav a{text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:.3rem}
.post-nav a small{font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;color:var(--copper);font-weight:600}
.post-nav a b{font-family:var(--display);font-weight:500;font-size:1.15rem}
.post-nav a:hover b{text-decoration:underline;text-underline-offset:3px}
.post-nav .next{text-align:right;align-items:flex-end}
@media (max-width:620px){.post-nav{grid-template-columns:1fr}.post-nav .next{text-align:left;align-items:flex-start}}
.byline{display:flex;align-items:center;gap:.8rem;margin-top:1.5rem;color:var(--muted);font-size:.9rem}
.byline img{width:40px;height:40px;border-radius:50%;object-fit:cover}

/* forms */
.form{display:grid;gap:1.1rem;max-width:720px}
.form .row{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media (max-width:620px){.form .row{grid-template-columns:1fr}}
.form label{display:grid;gap:.4rem;font-size:.85rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.form input,.form textarea{font:inherit;font-size:1rem;padding:.8rem .95rem;border:1px solid var(--paper-line);border-radius:var(--radius);background:#fff;color:var(--text);width:100%}
.form textarea{min-height:150px;resize:vertical}
.form input:focus,.form textarea:focus{border-color:var(--copper)}
.form-note{font-size:.88rem;color:var(--muted)}

/* CTA band */
.cta-band{background:var(--ink-2);color:var(--on-ink)}
.cta-band .wrap{display:grid;grid-template-columns:1fr auto;gap:1.5rem 3rem;align-items:center}
.cta-band h2{margin-top:.5rem}
@media (max-width:760px){.cta-band .wrap{grid-template-columns:1fr}}

/* stage band */
.stage-band{position:relative;min-height:380px;background:var(--ink);overflow:hidden;display:grid;place-items:end start;padding:0}
.stage-band img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.75}
.stage-band .wrap{position:relative;z-index:1;padding-block:2.5rem;width:100%;background:linear-gradient(180deg,transparent,rgba(18,16,16,.9))}
.stage-band h2{color:#fff;max-width:20ch}
.stage-band .btn-row{margin-top:1.2rem}

/* footer */
.site-footer{background:var(--ink);color:var(--on-ink-muted);padding-block:clamp(48px,6vw,80px) 2rem;border-top:1px solid var(--ink-line);font-size:.92rem}
.f-mission{padding-bottom:clamp(1.8rem,4vw,2.6rem);margin-bottom:clamp(2rem,4vw,3rem);border-bottom:1px solid var(--ink-line)}
.f-mission-label{font-size:.78rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--copper-glow);margin:0 0 .6rem}
.f-mission-text{font-family:var(--display);font-size:clamp(1.3rem,2.6vw,1.9rem);line-height:1.3;color:#fff;max-width:40ch;margin:0}
.site-footer .top{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:2.5rem}
.site-footer h4{color:#fff;font-family:var(--body);font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;margin-bottom:1rem}
.site-footer ul{list-style:none;margin:0;padding:0;display:grid;gap:.5rem}
.site-footer a{color:inherit;text-decoration:none}
.site-footer a:hover{color:#fff}
.site-footer .verse{font-family:var(--display);font-style:italic;font-size:1.15rem;line-height:1.4;color:var(--on-ink);max-width:38ch;margin-top:1.2rem}
.site-footer .verse cite{display:block;font-family:var(--body);font-style:normal;font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;margin-top:.8rem;color:var(--copper-glow)}
.site-footer .brand img{height:52px;width:52px}
.site-footer .brand span{color:#fff;font-size:1.2rem}
.site-footer .bottom{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--ink-line);display:flex;flex-wrap:wrap;gap:1rem 2rem;justify-content:space-between;font-size:.82rem}
.socials{display:flex;gap:.6rem}
.socials a{width:38px;height:38px;border:1px solid var(--ink-line);border-radius:50%;display:grid;place-items:center}
.socials a:hover{border-color:#fff}
.socials svg{width:17px;height:17px;fill:currentColor}
@media (max-width:860px){.site-footer .top{grid-template-columns:1fr 1fr}}
@media (max-width:520px){.site-footer .top{grid-template-columns:1fr}}
"""

JS = r"""
(function(){
  var t=document.querySelector('.nav-toggle'),n=document.getElementById('nav');
  if(t&&n){t.addEventListener('click',function(){var o=n.classList.toggle('is-open');t.setAttribute('aria-expanded',o?'true':'false');});}
  // Contact form: send in the background and go to the thanks page at once
  // (FormSubmit's own redirect can take 5-10 seconds). Falls back to a normal
  // post if fetch is missing or FormSubmit rejects the message.
  var form=document.querySelector('form.form');
  if(form&&window.fetch&&window.FormData&&/formsubmit\.co\//.test(form.action)){
    form.addEventListener('submit',function(e){
      e.preventDefault();
      var btn=form.querySelector('button[type=submit]');
      if(btn){btn.disabled=true;btn.textContent='Sending...';}
      var nextEl=form.querySelector('[name=_next]');
      var next=nextEl?nextEl.value:'/thanks/';
      var ajax=form.action.replace('formsubmit.co/','formsubmit.co/ajax/');
      var done=false;
      function go(){if(done)return;done=true;window.location.href=next;}
      function fallback(){if(done)return;done=true;form.submit();}
      var timer=setTimeout(go,1500);
      fetch(ajax,{method:'POST',body:new FormData(form),headers:{'Accept':'application/json'},keepalive:true})
        .then(function(r){return r.json().catch(function(){return {success:r.ok};});})
        .then(function(j){clearTimeout(timer);if(j&&(j.success===true||j.success==='true'))go();else fallback();})
        .catch(function(){clearTimeout(timer);fallback();});
    });
  }
  document.querySelectorAll('.video[data-yt]').forEach(function(v){
    v.addEventListener('click',function(e){
      e.preventDefault();
      var id=v.getAttribute('data-yt');
      var f=document.createElement('iframe');
      f.src='https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&rel=0';
      f.title=v.getAttribute('aria-label')||'YouTube video';
      f.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      f.allowFullscreen=true;
      v.innerHTML='';v.appendChild(f);
    });
  });
})();
"""

ICONS = {
    "ig": '<svg viewBox="0 0 24 24"><path d="M12 2.2c3.2 0 3.6 0 4.8.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1 .4 2.2.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 1.2-.2 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.2-1 .4-2.2.4-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-1.2-.1-1.8-.2-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.2-.4-.4-1-.4-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8c.1-1.2.2-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.2 1-.4 2.2-.4C8.4 2.2 8.8 2.2 12 2.2M12 0C8.7 0 8.3 0 7.1.1 5.8.1 4.9.3 4.1.6c-.8.3-1.5.7-2.1 1.4C1.3 2.6.9 3.3.6 4.1.3 4.9.1 5.8.1 7.1 0 8.3 0 8.7 0 12s0 3.7.1 4.9c.1 1.3.3 2.2.6 2.9.3.8.7 1.5 1.4 2.1.7.7 1.3 1.1 2.1 1.4.8.3 1.6.5 2.9.6 1.2.1 1.6.1 4.9.1s3.7 0 4.9-.1c1.3-.1 2.2-.3 2.9-.6.8-.3 1.5-.7 2.1-1.4.7-.7 1.1-1.3 1.4-2.1.3-.8.5-1.6.6-2.9.1-1.2.1-1.6.1-4.9s0-3.7-.1-4.9c-.1-1.3-.3-2.2-.6-2.9-.3-.8-.7-1.5-1.4-2.1C21.4 1.3 20.7.9 19.9.6 19.1.3 18.2.1 16.9.1 15.7 0 15.3 0 12 0zm0 5.8a6.2 6.2 0 1 0 0 12.4 6.2 6.2 0 0 0 0-12.4zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.4-11.8a1.4 1.4 0 1 0 0 2.9 1.4 1.4 0 0 0 0-2.9z"/></svg>',
    "fb": '<svg viewBox="0 0 24 24"><path d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.3l-.5 3.5h-2.8v8.4A12 12 0 0 0 24 12z"/></svg>',
    "yt": '<svg viewBox="0 0 24 24"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/></svg>',
    "spotify": '<svg viewBox="0 0 24 24"><path d="M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24zm5.5 17.3a.75.75 0 0 1-1 .25c-2.8-1.7-6.4-2.1-10.6-1.2a.75.75 0 1 1-.3-1.5c4.6-1 8.5-.6 11.7 1.4.3.2.4.7.2 1.1zm1.5-3.3a.94.94 0 0 1-1.3.3c-3.2-2-8.1-2.6-11.9-1.4a.94.94 0 1 1-.5-1.8c4.3-1.3 9.7-.7 13.4 1.6.4.3.6.9.3 1.3zm.1-3.4C15.3 8.3 9 8.1 5.3 9.2a1.13 1.13 0 1 1-.7-2.1c4.2-1.3 11.2-1 15.6 1.6a1.13 1.13 0 0 1-1.1 1.9z"/></svg>',
    "apple": '<svg viewBox="0 0 24 24"><path d="M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24zm1.9 20.3c-.2.7-.9 1.2-1.9 1.2s-1.7-.5-1.9-1.2l-.6-4.6c-.1-.8.3-1.5 1.2-1.7.8-.2 1.8-.2 2.6 0 .9.2 1.3.9 1.2 1.7l-.6 4.6zM12 12.8a2.3 2.3 0 1 1 0-4.6 2.3 2.3 0 0 1 0 4.6zm4.8 3.6-.9-.9c1-1.2 1.6-2.7 1.6-4.3 0-3.6-2.9-6.6-6.6-6.6S5.4 7.6 5.4 11.2c0 1.6.6 3.1 1.6 4.3l-.9.9a7.8 7.8 0 0 1-2-5.2c0-4.3 3.5-7.9 7.9-7.9s7.9 3.5 7.9 7.9c0 2-.8 3.8-2 5.2z"/></svg>',
    "amazon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/></svg>',
    "play": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
}

# ---------------------------------------------------------------- layout

def header(active, depth):
    links = []
    for path, label in NAV:
        cur = ' aria-current="page"' if path == active else ""
        links.append(f'<a href="{href(path, depth)}"{cur}>{label}</a>')
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{href('', depth)}" aria-label="Prodigal Man home"><img src="{asset('img/logo-180.png', depth)}" alt="" width="180" height="180"><span>Prodigal Man</span></a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav class="nav" id="nav" aria-label="Main">{''.join(links)}</nav>
  </div>
</header>"""


def footer(depth):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="f-mission">
      <p class="f-mission-label">The mission</p>
      <p class="f-mission-text">Fix the Lies. Fix the Man. Fix the World.</p>
    </div>
    <div class="top">
      <div>
        <a class="brand" href="{href('', depth)}"><img src="{asset('img/logo-180.png', depth)}" alt="" width="180" height="180"><span>Prodigal Man</span></a>
        <p class="verse">The Lord God placed the man in the Garden of Eden to tend and watch over it.<cite>Genesis 2:15</cite></p>
      </div>
      <div><h4>Explore</h4><ul>
        <li><a href="{href('book/', depth)}">Book</a></li>
        <li><a href="{href('podcast/', depth)}">Podcast</a></li>
        <li><a href="{href('speaking/', depth)}">Speaking</a></li>
        <li><a href="{href('blog/', depth)}">Blog</a></li>
      </ul></div>
      <div><h4>About</h4><ul>
        <li><a href="{href('more/about/', depth)}">Mission</a></li>
        <li><a href="{href('more/bio/', depth)}">Bio</a></li>
        <li><a href="{href('more/consulting/', depth)}">Consulting</a></li>
        <li><a href="{href('more/contact/', depth)}">Contact</a></li>
      </ul></div>
      <div><h4>Follow</h4><ul>
        <li><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram</a></li>
        <li><a href="{FACEBOOK}" target="_blank" rel="noopener">Facebook</a></li>
        <li><a href="{YT_CHANNEL}" target="_blank" rel="noopener">YouTube</a></li>
        <li><a href="{href('socials/', depth)}">All socials</a></li>
      </ul></div>
    </div>
    <div class="bottom">
      <span>&copy; 2026 Prodigal Man. All rights reserved.</span>
      <div class="socials">
        <a href="{INSTAGRAM}" target="_blank" rel="noopener" aria-label="Instagram">{ICONS['ig']}</a>
        <a href="{FACEBOOK}" target="_blank" rel="noopener" aria-label="Facebook">{ICONS['fb']}</a>
        <a href="{YT_CHANNEL}" target="_blank" rel="noopener" aria-label="YouTube">{ICONS['yt']}</a>
      </div>
    </div>
  </div>
</footer>"""


def page(path, title, description, body, active=None, hero_img=None, og_image=None):
    depth = path.count("/")
    active = path if active is None else active
    canonical = BASE_URL + path
    if og_image is None:
        key = {"": "home", "book/": "book", "podcast/": "podcast", "socials/": "socials", "speaking/": "speaking", "blog/": "blog", "more/about/": "about", "more/bio/": "bio", "more/consulting/": "consulting", "more/contact/": "contact"}.get(path)
        if key is None and path.startswith("blog/"):
            key = "post-" + path[len("blog/"):].strip("/")
        og_image = f"share/{key}.jpg" if key else "share/home.jpg"
    full_title = "Prodigal Man" if path == "" else f"{title} | Prodigal Man"
    hero_style = f'<style>.hero::before,.page-hero::before{{background-image:url({asset("img/" + hero_img, depth)})}}</style>' if hero_img else ""
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="Prodigal Man">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE_URL}assets/{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{BASE_URL}assets/{og_image}">
<meta name="theme-color" content="#121010">
<link rel="icon" type="image/png" href="{asset('img/favicon.png', depth)}">
<link rel="apple-touch-icon" href="{asset('img/logo-180.png', depth)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT@0,9..144,300..700,0..100;1,9..144,300..700,0..100&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{asset('site.css', depth)}">
{hero_style}
</head>
<body>
{header(active, depth)}
<main>
{body}
</main>
{footer(depth)}
<script src="{asset('site.js', depth)}" defer></script>
</body>
</html>
"""
    out = os.path.join(SITE, path, "index.html") if path else os.path.join(SITE, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


def page_hero(eyebrow, title, lede, depth, crumbs=None):
    c = ""
    if crumbs:
        c = '<p class="crumbs">' + " / ".join(crumbs) + "</p>"
    return f"""<section class="page-hero">
  <div class="wrap">
    {c}
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title}</h1>
    {f'<p class="lede">{lede}</p>' if lede else ''}
  </div>
</section>"""


def video(vid, label, depth, extra_cls=""):
    embed = "" if FILE_LINKS else f' data-yt="{vid}"'
    return f"""<a class="video {extra_cls}" href="https://youtu.be/{vid}" target="_blank" rel="noopener"{embed} aria-label="{esc(label)}">
  <img src="{yt_thumb(vid, depth)}" alt="" loading="lazy" width="480" height="360">
  <span class="play"></span>
</a>"""


def contact_form(depth, heading=True):
    h = ""
    if heading:
        h = """<div class="section-head"><div>
      <p class="eyebrow">Contact</p>
      <h2>Book Tim to speak</h2>
      <p class="lede">Men's conferences, church men's ministries, retreats and leadership events. Send a note and Tim will get back to you.</p>
    </div></div>"""
    return f"""{h}
    <form class="form" method="post" action="{FORM_ENDPOINT}">
      <input type="hidden" name="_subject" value="New message from prodigalman.com">
      <input type="hidden" name="_template" value="table">
      <input type="hidden" name="_cc" value="arv1221@gmail.com">
      <input type="hidden" name="_captcha" value="false">
      <input type="hidden" name="_next" value="{BASE_URL}thanks/">
      <input type="text" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true" style="display:none">
      <div class="row">
        <label>Name<input type="text" name="name" autocomplete="name" required></label>
        <label>Email<input type="email" name="email" autocomplete="email" required></label>
      </div>
      <label>Phone<input type="tel" name="phone" autocomplete="tel"></label>
      <label>Message<textarea name="message" required></textarea></label>
      <div class="btn-row">
        <button class="btn btn-primary" type="submit">Contact Prodigal Man {ICONS['arrow']}</button>
        <span class="form-note">Or message Tim on <a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram</a>.</span>
      </div>
    </form>"""


def cta_band(depth, eyebrow, title, btn_label, btn_href, ghost=None):
    g = f'<a class="btn btn-ghost" href="{ghost[1]}">{ghost[0]}</a>' if ghost else ""
    return f"""<section class="cta-band">
  <div class="wrap">
    <div><p class="eyebrow">{eyebrow}</p><h2>{title}</h2></div>
    <div class="btn-row"><a class="btn btn-primary" href="{btn_href}">{btn_label} {ICONS['arrow']}</a>{g}</div>
  </div>
</section>"""


# ---------------------------------------------------------------- pages

def build_home():
    d = 0
    featured = posts[5]  # Choose Your Soil, the post the original site features
    body = f"""
<section class="hero home-hero">
  <div class="wrap">
    <div>
      <p class="eyebrow">Tim Couet &middot; Prodigal Man</p>
      <h1>Fix the Lies. Fix the <em>Man</em>. Fix the World.</h1>
      <p class="lede">Calling the men of the Church home to the identity God assigned them, so they can walk in victory as husbands, fathers and leaders.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="{href('book/', d)}">{ICONS['amazon']} Get the book</a>
        <a class="btn btn-ghost" href="{href('more/contact/', d)}">Book Tim to speak</a>
      </div>
      <div class="hero-roles"><span>Jesus Follower</span><span>Husband</span><span>Father</span><span>Speaker</span><span>Author</span><span>Leadership Coach</span></div>
    </div>
    <figure class="poster">
      <img src="{asset('img/tim-portrait.jpg', d)}" alt="Tim Couet" width="445" height="458">
      <figcaption><b>Tim Couet</b> &middot; Author of Identity Assignment</figcaption>
    </figure>
  </div>
</section>

<section>
  <div class="wrap split">
    <div>
      <p class="eyebrow">Who we are</p>
      <h2>Equipping men to win</h2>
      <p class="lede" style="margin-top:1rem">Prodigal Man was born out of the deep need for the men of the Church to reclaim victory in their lives. It starts with fixing the identity God assigned to men in the Garden of Eden, and from that identity learning how to lead at home, in the church and in the community.</p>
      <div class="btn-row" style="margin-top:1.5rem">
        <a class="link" href="{href('more/about/', d)}">Read the mission {ICONS['arrow']}</a>
        <a class="link" href="{href('more/bio/', d)}">Meet Tim {ICONS['arrow']}</a>
      </div>
    </div>
    <div style="display:grid;justify-items:center;gap:1.2rem;text-align:center">
      <img class="logo-round" src="{asset('img/logo.png', d)}" alt="The Prodigal Man" width="569" height="576">
      <p class="tagline">Fix the Lies. <b>Fix the Man.</b> Fix the World.</p>
    </div>
  </div>
</section>

<section class="ink" id="connect">
  <div class="wrap">
    <div class="section-head"><div>
      <p class="eyebrow">Connect</p>
      <h2>Featured content</h2>
      <p class="lede">Messages, reels and writing to help you walk in victory in every area of your life.</p>
    </div></div>
    <div class="grid grid-3">
      <a class="tile" href="{YT_CHANNEL}" target="_blank" rel="noopener">
        <img src="{asset('img/clarity-confusion.jpg', d)}" alt="Tim Couet speaking under a Clarity | Confusion title" width="900" height="756" loading="lazy">
        <div class="tile-body"><span class="pill">YouTube</span><h3>Clarity over confusion</h3><p>Full messages from men's ministry nights and conferences.</p><span class="link">Watch on YouTube {ICONS['arrow']}</span></div>
      </a>
      <a class="tile" href="{INSTAGRAM}" target="_blank" rel="noopener">
        <img src="{asset('img/build-strong-boys.jpg', d)}" alt="Build Strong Boys reel cover" width="740" height="665" loading="lazy">
        <div class="tile-body"><span class="pill">Instagram</span><h3>Build strong boys</h3><p>Short reels for fathers raising sons in a battlefield culture.</p><span class="link">Follow @prodigalman {ICONS['arrow']}</span></div>
      </a>
      <a class="tile" href="{href('blog/' + featured['slug'] + '/', d)}">
        <img src="{asset('img/sprout.jpg', d)}" alt="Seedlings sprouting from soil" width="480" height="480" loading="lazy">
        <div class="tile-body"><span class="pill">Blog</span><h3>{esc(featured['title'])}</h3><p>{esc(excerpt(featured['paragraphs'], 110))}</p><span class="link">Read the post {ICONS['arrow']}</span></div>
      </a>
    </div>
  </div>
</section>

<section class="stage-band">
  <img src="{asset('img/stage-wide.jpg', d)}" alt="" width="1282" height="431" loading="lazy">
  <div class="wrap">
    <p class="eyebrow">Speaking</p>
    <h2>Bring Tim to your church or men's event</h2>
    <div class="btn-row"><a class="btn btn-light" href="{href('speaking/', d)}">{ICONS['play']} Watch Tim speak</a><a class="btn btn-ghost" href="{href('more/contact/', d)}">Book Tim</a></div>
  </div>
</section>

<section id="contact">
  <div class="wrap">
    {contact_form(d)}
  </div>
</section>
"""
    page("", "Prodigal Man", "Tim Couet, Prodigal Man: speaker, author and leadership coach calling the men of the Church home to the identity God assigned them. Fix the Lies. Fix the Man. Fix the World.", body, active="", hero_img="stage-wide.jpg")


def build_book():
    d = 1
    body = page_hero("Book", "Identity Assignment", "Now available. Tim Couet's book on the foundation of manhood: the identity God assigned to men in the garden, and how to live from it today.", d) + f"""
<section>
  <div class="wrap split">
    <figure class="book-cover"><img src="{asset('img/book-cover.png', d)}" alt="Identity Assignment by Tim Couet, book cover and stacked copies" width="864" height="1200"></figure>
    <div>
      <p class="eyebrow">Now available</p>
      <h2>Identity Assignment</h2>
      <p class="lede" style="margin-top:1rem">By Tim Couet. Order your copy on Amazon.</p>
      <div class="btn-row" style="margin-top:1.75rem">
        <a class="btn btn-primary" href="{AMAZON}" target="_blank" rel="noopener">{ICONS['amazon']} Buy now on Amazon</a>
        <a class="btn btn-ghost" href="{href('speaking/', d)}">Watch the message</a>
      </div>
      <p class="muted" style="margin-top:2rem;font-size:.95rem">Want Tim to teach this material at your church or men's event? <a href="{href('more/contact/', d)}">Get in touch</a>.</p>
    </div>
  </div>
</section>
""" + cta_band(d, "Go deeper", "Read the blog series on identity", "Read the blog", href("blog/", d))
    page("book/", "Book", "Identity Assignment by Tim Couet is now available on Amazon.", body, hero_img="studio.jpg")


def build_podcast():
    d = 1
    body = page_hero("Podcasts", "Listen in", "Altar'd Manhood and The Mentoring Christian Men Worldwide Podcast, on Spotify, Apple Podcasts and YouTube.", d) + f"""
<section class="ink">
  <div class="wrap">
    <div class="show">
      <img src="{asset('img/altard-manhood.jpg', d)}" alt="Altar'd Manhood podcast cover with the three hosts" width="900" height="900">
      <div>
        <p class="eyebrow">Now available</p>
        <h3>Altar'd Manhood</h3>
        <p class="lede">Three men, one table, real conversations about following Jesus as a man.</p>
        <div class="btn-row" style="margin-top:1.5rem">
          <a class="btn btn-primary" href="https://youtu.be/ELyW6Yx8xvw" target="_blank" rel="noopener">{ICONS['play']} Watch on YouTube</a>
          <a class="btn btn-ghost" href="https://open.spotify.com/show/6KixGA0uXD8UXjCUspgu6I" target="_blank" rel="noopener">{ICONS['spotify']} Spotify</a>
          <a class="btn btn-ghost" href="https://podcasts.apple.com/us/podcast/altard-manhood/id1761560534" target="_blank" rel="noopener">{ICONS['apple']} Apple Podcasts</a>
        </div>
      </div>
    </div>
    <div class="show">
      <img src="{asset('img/mentoring-christian-men.jpg', d)}" alt="The Mentoring Christian Men Worldwide Podcast cover, a gold globe on black" width="900" height="900">
      <div>
        <p class="eyebrow">Now available</p>
        <h3>The Mentoring Christian Men Worldwide Podcast</h3>
        <p class="lede">With Tim Couet and Christian Lenty.</p>
        <div class="btn-row" style="margin-top:1.5rem">
          <a class="btn btn-primary" href="https://open.spotify.com/show/1RQPCJdlEivy6tsnvgVnFL" target="_blank" rel="noopener">{ICONS['spotify']} Spotify</a>
          <a class="btn btn-ghost" href="https://podcasts.apple.com/us/podcast/q-a-with-t-c/id1785710164" target="_blank" rel="noopener">{ICONS['apple']} Apple Podcasts</a>
        </div>
      </div>
    </div>
  </div>
</section>
""" + cta_band(d, "More from Tim", "Watch the full messages", "Go to Speaking", href("speaking/", d))
    page("podcast/", "Podcast", "Altar'd Manhood and The Mentoring Christian Men Worldwide Podcast, Tim Couet's shows, on Spotify, Apple Podcasts and YouTube.", body, hero_img="panel.jpg")


def build_socials():
    d = 1
    body = page_hero("Socials", "Follow along", "Daily encouragement for men on Instagram, Facebook and YouTube.", d) + f"""
<section>
  <div class="wrap">
    <div class="grid grid-3">
      <a class="social-card" href="{INSTAGRAM}" target="_blank" rel="noopener">
        <span class="ico">{ICONS['ig']}</span><h3>Instagram</h3><p>@prodigalman. Reels and posts for husbands, fathers and leaders.</p><span class="link">View profile {ICONS['arrow']}</span>
      </a>
      <a class="social-card" href="{FACEBOOK}" target="_blank" rel="noopener">
        <span class="ico">{ICONS['fb']}</span><h3>Facebook</h3><p>Prodigal Man Ministries. Updates, events and the timeline.</p><span class="link">Visit the page {ICONS['arrow']}</span>
      </a>
      <a class="social-card" href="{YT_CHANNEL}?sub_confirmation=1" target="_blank" rel="noopener">
        <span class="ico">{ICONS['yt']}</span><h3>YouTube</h3><p>Full messages, podcast episodes and teaching.</p><span class="link">Subscribe {ICONS['arrow']}</span>
      </a>
    </div>
  </div>
</section>
<section class="ink">
  <div class="wrap">
    <div class="section-head"><div>
      <p class="eyebrow">Featured video</p>
      <h2>New Life, New Creation</h2>
    </div><a class="btn btn-ghost" href="{YT_CHANNEL}?sub_confirmation=1" target="_blank" rel="noopener">{ICONS['yt']} Subscribe on YouTube</a></div>
    {video('2idn0svegWw', 'New Life, New Creation, a message by Tim Couet', d)}
  </div>
</section>
"""
    page("socials/", "Socials", "Follow Tim Couet and Prodigal Man on Instagram, Facebook and YouTube.", body, hero_img="studio-blue.jpg")


def build_speaking():
    d = 1
    talks = [
        ("jjnwavlpyaY", "Identity Assignment", "The Foundation of Manhood", "Where manhood starts: the identity God assigned to men in the garden."),
        ("2idn0svegWw", "New Life, New Creation", "", "What changes when a man is made new in Christ."),
        ("JFrqmjEveAI", "Trust, Choices, Promises, Lies, Victory", "Part 1", "Walking in God's promises instead of the enemy's lies."),
    ]
    items = []
    for vid, title, sub, blurb in talks:
        s = f'<p class="eyebrow">{esc(sub)}</p>' if sub else '<p class="eyebrow">Message</p>'
        items.append(f"""<div class="talk">
      {video(vid, title, d)}
      <div>{s}<h3>{esc(title)}</h3><p class="lede">{esc(blurb)}</p><a class="link" href="https://youtu.be/{vid}" target="_blank" rel="noopener" style="margin-top:1rem">Open on YouTube {ICONS['arrow']}</a></div>
    </div>""")
    body = page_hero("Speaking", "Watch Tim speak", "Messages from men's conferences and church men's ministries. Book Tim for your next event.", d) + f"""
<section>
  <div class="wrap">
    {''.join(items)}
    <div class="btn-row" style="margin-top:3rem"><a class="btn btn-ghost" href="{YT_CHANNEL}?sub_confirmation=1" target="_blank" rel="noopener">{ICONS['yt']} Subscribe on YouTube</a></div>
  </div>
</section>
""" + cta_band(d, "Book Tim", "Bring this message to your men", "Book Tim to speak", href("more/contact/", d), ("Free church consulting", href("more/consulting/", d)))
    page("speaking/", "Speaking", "Watch Tim Couet's messages on identity, new creation and victory, and book him for your men's event.", body, hero_img="stage-2.jpg")


def build_about():
    d = 2
    body = page_hero("Mission", "The mission", "Why Prodigal Man exists.", d) + f"""
<section>
  <div class="wrap split">
    <div class="prose">
      <p>Prodigal Man has been born out of the deep need for the men of the Church to reclaim victory in their lives. Too long has the enemy had his way leading men astray into emptiness, frustration and shame.</p>
      <p>We have been created to chase God's great rewards, grow His kingdom and enjoy His victories in our lives. We do this first by fixing our identity that was assigned to us in the Garden of Eden. From that identity we know how to operate in the world around us and how to defeat Satan's tactics.</p>
      <p>We learn how to lead our wives, how to lead our children, how to lead other men around us, how to lead in our churches and how to lead in our communities.</p>
      <p>The world has done its best to redefine masculinity so that it could label it toxic. We are here to reclaim it for God's glory and to make it a blessing for the world.</p>
      <p>If you're a man reading this, join us in the journey, and learn how to walk in victory in every area of your life.</p>
    </div>
    <div style="display:grid;justify-items:center;gap:1.2rem;text-align:center">
      <img class="logo-round" src="{asset('img/logo.png', d)}" alt="The Prodigal Man" width="569" height="576" style="width:220px;height:220px">
      <p class="tagline">Fix the Lies. <b>Fix the Man.</b> Fix the World.</p>
    </div>
  </div>
</section>
""" + cta_band(d, "Join the journey", "Start with the identity God gave you", "Read the blog", href("blog/", d), ("Meet Tim", href("more/bio/", d)))
    page("more/about/", "Mission", "The mission of Prodigal Man: reclaiming victory for the men of the Church by fixing identity first.", body, hero_img="stage-wide.jpg")


def build_bio():
    d = 2
    body = page_hero("Bio", "Meet Tim Couet", "Jesus follower, husband, father, speaker, author and leadership coach.", d) + f"""
<section>
  <div class="wrap split" style="align-items:start">
    <div class="prose">
      <p>Hi and thank you for visiting my site today. I'm first and foremost a husband to my wife and a father to four amazing children. I was sitting in church one Saturday evening and was overcome with the feeling of being called into men's ministry. God showed me that the church is full of prodigal men that desire to experience God's victory in their life but they've settled for a mediocre existence. To back track, I grew up in a loving catholic home. I came into a personal relationship with our savior, Jesus Christ, while I was playing college baseball through the great ministry of Cru formerly known as Campus Crusade for Christ. I graduated college feeling called into ministry, but God chose a different path for me.</p>
      <p>I started my career in the government and political world, I developed relationships with some righteous men who were leaders, and I also saw the broken world of men and women around me. As my desire to serve grew, I served on a local crisis pregnancy center's board. This ministry was full of brokenness but also miracles. I saw so many women who were abused and abandoned by men. This began my journey to being God's servant in fixing this world by fixing a man's identity. If a man doesn't know his assigned identity by God he will always struggle. My true desire is to help men win in this world, all to grow God's Kingdom and to reestablish that our masculinity has been created to be a blessing to the world. I truly hope that every word I say and every action I do, brings glory to God and grows the men of the church into the warriors God intends them to be.</p>
      <p>I'm excited to help you grow closer to the King of the Universe and learn how to walk in victory in every area of your life.</p>
      <p><em>Tim</em></p>
    </div>
    <div style="display:grid;gap:1.2rem">
      <img src="{asset('img/tim-portrait.jpg', d)}" alt="Tim Couet" width="445" height="458" style="border-radius:8px;box-shadow:0 30px 60px -20px rgba(0,0,0,.5)">
      <ul class="roles"><li>Jesus Follower</li><li>Husband</li><li>Father</li><li>Speaker</li><li>Author</li><li>Leadership Coach</li></ul>
    </div>
  </div>
</section>
""" + cta_band(d, "Work with Tim", "Book Tim for your church or event", "Contact Tim", href("more/contact/", d), ("Read the book", href("book/", d)))
    page("more/bio/", "Bio", "Tim Couet's story: from college baseball and Cru to government, a crisis pregnancy center board, and a calling into men's ministry.", body, hero_img="studio.jpg")


def build_consulting():
    d = 2
    body = page_hero("Consulting", "Men's ministry consulting for churches", "Free consultations for churches looking to start, restart or grow their men's ministry.", d) + f"""
<section>
  <div class="wrap split" style="align-items:start">
    <div class="prose">
      <p>One of the main goals of Prodigal Man is to assist churches in creating, growing and developing a successful men's ministry. Men are traditionally seen as difficult to reach and hard to get to show up. As such, many churches shy away from giving their attention to the foundation of their church, men. I believe men do want to show. They do want success and they do crave other brothers to go shoulder to shoulder with in the battle against the enemy. That's where proper messaging and infrastructure comes into play.</p>
      <p>Prodigal Man offers FREE consultations for churches looking to start, restart, or grow their men's ministry. Contact me today and allow my years of men's ministry experience help us grow God's Kingdom together.</p>
    </div>
    <div class="grid">
      <div class="card"><span class="pill">Start</span><h3>Launch a men's ministry</h3><p class="muted">Messaging and structure that gets men in the room and keeps them coming back.</p></div>
      <div class="card"><span class="pill">Restart</span><h3>Relaunch what stalled</h3><p class="muted">A fresh look at why men stopped showing up and how to win them back.</p></div>
      <div class="card"><span class="pill">Grow</span><h3>Multiply leaders</h3><p class="muted">Raise up group leaders and build infrastructure that scales.</p></div>
    </div>
  </div>
</section>
""" + cta_band(d, "Free consultation", "Let's grow God's Kingdom together", "Contact Tim", href("more/contact/", d))
    page("more/consulting/", "Consulting", "Prodigal Man offers free consultations for churches that want to start, restart or grow their men's ministry.", body, hero_img="panel.jpg")


def build_contact():
    d = 2
    body = page_hero("Contact", "Book Tim to speak", "Conferences, men's ministry nights, retreats, podcasts and church consulting.", d) + f"""
<section>
  <div class="wrap">
    {contact_form(d, heading=False)}
  </div>
</section>
<section class="ink">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Other ways to reach Tim</p><h2>Find Prodigal Man online</h2></div></div>
    <div class="grid grid-3">
      <a class="tile" href="{INSTAGRAM}" target="_blank" rel="noopener"><div class="tile-body"><span class="pill">Instagram</span><h3>@prodigalman</h3><span class="link">Send a message {ICONS['arrow']}</span></div></a>
      <a class="tile" href="{FACEBOOK}" target="_blank" rel="noopener"><div class="tile-body"><span class="pill">Facebook</span><h3>Prodigal Man Ministries</h3><span class="link">Visit the page {ICONS['arrow']}</span></div></a>
      <a class="tile" href="{YT_CHANNEL}" target="_blank" rel="noopener"><div class="tile-body"><span class="pill">YouTube</span><h3>Prodigal Man</h3><span class="link">Watch and subscribe {ICONS['arrow']}</span></div></a>
    </div>
  </div>
</section>
"""
    page("more/contact/", "Contact", "Book Tim Couet to speak at your church, men's conference or event.", body, hero_img="stage-2.jpg")


def build_blog():
    d = 1
    first = posts[0]
    cards = []
    for i, p in enumerate(posts[1:], start=2):
        cards.append(f"""<a class="post-card" href="{href('blog/' + p['slug'] + '/', d)}">
        <span class="num">Post {i:02d}</span>
        <h3>{esc(p['title'])}</h3>
        <p>{esc(excerpt(p['paragraphs']))}</p>
        <span class="link">Read {ICONS['arrow']}</span>
      </a>""")
    body = page_hero("Blog", "Writing for men of the Church", "Identity, victory, protection and the promises of God, written by Tim Couet for men who want to win.", d) + f"""
<section>
  <div class="wrap">
    <a class="post-feature" href="{href('blog/' + first['slug'] + '/', d)}" style="text-decoration:none;color:inherit">
      <img src="{asset('img/studio.jpg', d)}" alt="" width="1443" height="640" loading="lazy">
      <div>
        <p class="eyebrow">Start here &middot; Post 01</p>
        <h2>{esc(first['title'])}</h2>
        <p class="lede">{esc(excerpt(first['paragraphs'], 220))}</p>
        <span class="link" style="margin-top:1.2rem">Read the post {ICONS['arrow']}</span>
      </div>
    </a>
    <div class="post-grid">
      {''.join(cards)}
    </div>
  </div>
</section>
""" + cta_band(d, "Keep going", "Get the book: Identity Assignment", "Buy on Amazon", AMAZON)
    page("blog/", "Blog", "Blog posts by Tim Couet on identity, victory and the promises of God for men.", body, hero_img="studio.jpg")

    for i, p in enumerate(posts):
        d = 2
        prev_p = posts[i - 1] if i > 0 else None
        next_p = posts[i + 1] if i < len(posts) - 1 else None
        nav = '<nav class="post-nav" aria-label="More posts">'
        nav += (f'<a href="{href("blog/" + prev_p["slug"] + "/", d)}"><small>Previous</small><b>{esc(prev_p["title"])}</b></a>' if prev_p else "<span></span>")
        nav += (f'<a class="next" href="{href("blog/" + next_p["slug"] + "/", d)}"><small>Next</small><b>{esc(next_p["title"])}</b></a>' if next_p else "<span></span>")
        nav += "</nav>"
        body = page_hero("Blog", esc(p["title"]), "", d, crumbs=[f'<a href="{href("", d)}">Home</a>', f'<a href="{href("blog/", d)}">Blog</a>', f"Post {i + 1:02d}"]) + f"""
<section>
  <div class="wrap narrow">
    <div class="prose">
      {para_html(p['paragraphs'])}
    </div>
    <div class="byline"><img src="{asset('img/tim-portrait.jpg', d)}" alt="" width="40" height="40"><span>By Tim Couet &middot; Prodigal Man</span></div>
    {nav}
  </div>
</section>
""" + cta_band(d, "Share this", "Know a man who needs this? Send it to him.", "All blog posts", href("blog/", d), ("Get the book", href("book/", d)))
        page("blog/" + p["slug"] + "/", p["title"], excerpt(p["paragraphs"], 155), body, active="blog/", hero_img="stage-wide.jpg")


def build_extras():
    with open(os.path.join(SITE, "assets", "site.css"), "w", encoding="utf-8") as f:
        f.write(CSS.strip() + "\n")
    with open(os.path.join(SITE, "assets", "site.js"), "w", encoding="utf-8") as f:
        f.write(JS.strip() + "\n")
    paths = ["", "book/", "podcast/", "socials/", "blog/", "speaking/", "more/about/", "more/bio/", "more/consulting/", "more/contact/"] + ["blog/" + p["slug"] + "/" for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{BASE_URL}{p}</loc></url>\n" for p in paths)
    sm += "</urlset>\n"
    open(os.path.join(SITE, "sitemap.xml"), "w").write(sm)
    open(os.path.join(SITE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /thanks/\nSitemap: {BASE_URL}sitemap.xml\n")
    # 404
    body = page_hero("404", "Page not found", "That page has moved or never existed.", 0)
    body += f'<section><div class="wrap"><div class="btn-row"><a class="btn btn-primary" href="{href("", 0)}">Back home</a><a class="btn btn-ghost" href="{href("blog/", 0)}">Read the blog</a></div></div></section>'
    page("", "Page not found", "Page not found.", body, active="zzz")
    os.replace(os.path.join(SITE, "index.html"), os.path.join(SITE, "404.html"))
    # thank-you page the contact form redirects to (noindex, not in the sitemap)
    body = page_hero("Contact", "Thanks, your message is on its way", "Tim will get back to you soon.", 1)
    body += f'<section><div class="wrap"><div class="btn-row"><a class="btn btn-primary" href="{href("", 1)}">Back home</a><a class="btn btn-ghost" href="{href("blog/", 1)}">Read the blog</a><a class="btn btn-ghost" href="{href("speaking/", 1)}">Watch Tim speak</a></div></div></section>'
    page("thanks/", "Message sent", "Thanks for contacting Prodigal Man.", body, active="more/contact/")
    t = os.path.join(SITE, "thanks", "index.html")
    html_t = open(t, encoding="utf-8").read().replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"', 1)
    open(t, "w", encoding="utf-8").write(html_t)


def main():
    # clear generated html, keep assets
    for root, dirs, files in os.walk(SITE):
        if "assets" in root:
            continue
        for fn in files:
            if fn.endswith((".html", ".xml", ".txt")):
                os.remove(os.path.join(root, fn))
    build_extras()
    build_home()
    build_book()
    build_podcast()
    build_socials()
    build_speaking()
    build_about()
    build_bio()
    build_consulting()
    build_contact()
    build_blog()
    n = sum(len([f for f in fs if f.endswith(".html")]) for _, _, fs in os.walk(SITE))
    print(f"built {n} pages into {SITE} ({'file' if FILE_LINKS else 'folder'} links)")


if __name__ == "__main__":
    main()
