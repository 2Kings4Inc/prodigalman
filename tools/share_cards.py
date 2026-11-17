#!/usr/bin/env python3
"""Render 1200x630 Open Graph share cards into site/assets/share/.
Needs Pillow (pip install pillow). Run from the project folder: python3 tools/share_cards.py
"""
import json, os, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "site", "assets", "img")
OUT = os.path.join(ROOT, "site", "assets", "share")
FONTS = os.path.join(ROOT, "tools", "fonts")
W, H = 1200, 630
INK = (18, 16, 16); COPPER = (194, 100, 31); GLOW = (233, 165, 103); MUTED = (179, 168, 159); WHITE = (245, 240, 234)
os.makedirs(OUT, exist_ok=True)

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)

F_DISPLAY = lambda s: font("Fraunces-Medium.ttf", s)
F_LABEL = lambda s: font("HankenGrotesk-SemiBold.ttf", s)
F_BODY = lambda s: font("HankenGrotesk-Medium.ttf", s)

def cover(path, size, opacity):
    im = Image.open(path).convert("RGB")
    r = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    x = (im.width - size[0]) // 2; y = (im.height - size[1]) // 2
    im = im.crop((x, y, x + size[0], y + size[1]))
    base = Image.new("RGB", size, INK)
    return Image.blend(base, im, opacity)

def background(photo="stage-wide.jpg"):
    bg = cover(os.path.join(IMG, photo), (W, H), 0.35)
    # copper glow top-right, dark fade bottom
    glow = Image.new("RGB", (W, H), INK)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W - 520, -260, W + 180, 400), fill=(70, 36, 14))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    bg = Image.blend(bg, glow, 0.0) if False else Image.composite(bg, bg, Image.new("L", (W, H), 255))
    bg = Image.fromarray(__import__("numpy").clip(__import__("numpy").asarray(bg).astype(int) + __import__("numpy").asarray(glow).astype(int) - 18, 0, 255).astype("uint8")) if _has_numpy() else bg
    fade = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fade)
    for i in range(H):
        fd.line((0, i, W, i), fill=int(255 * min(1, max(0, (i - H * 0.35) / (H * 0.65))) * 0.85))
    bg = Image.composite(Image.new("RGB", (W, H), INK), bg, fade)
    return bg

def _has_numpy():
    try:
        import numpy; return True
    except Exception:
        return False

def draw_brand(d, im):
    logo = Image.open(os.path.join(IMG, "logo-180.png")).convert("RGBA").resize((64, 64), Image.LANCZOS)
    im.paste(logo, (72, 56), logo)
    d.text((152, 70), "Prodigal Man", font=F_DISPLAY(34), fill=WHITE)

def wrap(text, fnt, max_w, d):
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def card(name, eyebrow, title, sub=None, photo="stage-wide.jpg", side=None, side_round=False, side_raw=False):
    im = background(photo); d = ImageDraw.Draw(im)
    draw_brand(d, im)
    text_w = 700 if side else 1040
    # eyebrow
    d.text((72, 190), eyebrow.upper(), font=F_LABEL(22), fill=GLOW, spacing=4)
    # title: shrink until it fits in 3 lines
    size = 76
    while True:
        fnt = F_DISPLAY(size); lines = wrap(title, fnt, text_w, d)
        if len(lines) <= 2 or size <= 48: break
        size -= 4
    y = 236
    for ln in lines:
        d.text((70, y), ln, font=fnt, fill=WHITE); y += int(size * 1.12)
    if sub and y + 90 <= H - 100:
        sf = F_BODY(26); y += 14
        for ln in wrap(sub, sf, text_w, d)[:2]:
            d.text((72, y), ln, font=sf, fill=MUTED); y += 36
    # footer
    d.line((72, H - 86, W - 72, H - 86), fill=(60, 52, 48), width=1)
    d.text((72, H - 66), "prodigalman.com", font=F_LABEL(22), fill=MUTED)
    tag = "Fix the Lies. Fix the Man. Fix the World."
    tf = F_DISPLAY(24); d.text((W - 72 - d.textlength(tag, font=tf), H - 68), tag, font=tf, fill=GLOW)
    if side:
        s = Image.open(os.path.join(IMG, side)).convert("RGBA")
        box = (340, 340) if side_raw else (300, 300) if side_round else (300, int(300 * s.height / s.width)) if s.width >= s.height else (int(330 * s.width / s.height), 330)
        s = s.resize(box, Image.LANCZOS)
        if side_raw:
            pass
        elif side_round:
            m = Image.new("L", box, 0); ImageDraw.Draw(m).ellipse((0, 0, box[0] - 1, box[1] - 1), fill=255); s.putalpha(m)
        else:
            m = Image.new("L", box, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, box[0] - 1, box[1] - 1), 14, fill=255); s.putalpha(m)
        sh = Image.new("RGBA", (box[0] + 80, box[1] + 80), (0, 0, 0, 0))
        if side_raw:
            sh.paste((0, 0, 0, 170), (40, 50, box[0] + 40, box[1] + 50), s)
        else:
            ImageDraw.Draw(sh).rounded_rectangle((40, 50, box[0] + 40, box[1] + 50), 16, fill=(0, 0, 0, 160))
        sh = sh.filter(ImageFilter.GaussianBlur(22))
        x = W - 72 - box[0]; yy = (H - 60 - box[1]) // 2 + 20
        im.paste(sh, (x - 40, yy - 40), sh); im.paste(s, (x, yy), s)
    im.save(os.path.join(OUT, name + ".jpg"), quality=86, optimize=True)
    print("share card", name)

posts = json.load(open(os.path.join(ROOT, "content", "posts.json"), encoding="utf-8"))

card("home", "Tim Couet", "Fix the Lies. Fix the Man. Fix the World.", "Speaker, author and leadership coach calling the men of the Church home.", side="tim-portrait.jpg")
card("book", "The book", "Identity Assignment", "By Tim Couet. Now available on Amazon.", photo="studio.jpg", side="book-cover.png", side_raw=True)
card("podcast", "Podcasts", "Altar'd Manhood and The Mentoring Christian Men Worldwide Podcast", "On Spotify, Apple Podcasts and YouTube.", photo="panel.jpg", side="mentoring-christian-men.jpg")
card("socials", "Socials", "Follow Prodigal Man", "Instagram, Facebook and YouTube.", photo="studio-blue.jpg", side="logo.png", side_round=True)
card("speaking", "Speaking", "Book Tim to speak at your men's event", "Identity Assignment, New Life New Creation, and more.", photo="stage-2.jpg")
card("blog", "Blog", "Writing for men of the Church", "Identity, victory and the promises of God.", photo="studio.jpg")
card("about", "Mission", "The mission of Prodigal Man", "Reclaiming victory for the men of the Church.", side="logo.png", side_round=True)
card("bio", "Bio", "Meet Tim Couet", "Jesus follower, husband, father, speaker, author, leadership coach.", photo="studio.jpg", side="tim-portrait.jpg")
card("consulting", "Consulting", "Free men's ministry consulting for churches", "Start, restart or grow your men's ministry.", photo="panel.jpg")
card("contact", "Contact", "Book Tim to speak", "Conferences, men's nights, retreats and church consulting.", photo="stage-2.jpg")
for p in posts:
    card("post-" + p["slug"], "Blog  ·  Tim Couet", p["title"], photo="stage-wide.jpg")
