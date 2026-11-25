# Prodigal Man (prodigalman.com rebuild)

Static rebuild of https://prodigalman.com/ (Tim Couet) in the look of foreverchanged.vercel.app.
Built Nov 17, 2026. Not a 2 Kings 4 Inc brand; client work.

- `build.py` generates `site/` from `content/posts.json` (11 blog posts scraped from the live site). No dependencies.
- `python3 build.py` for folder-style links (`/book/`), `python3 build.py --file` for explicit `index.html` links (artifact previews).
- `site/` is committed so it can be deployed as-is. Vercel: output directory `site`, framework none, `vercel.json` at this folder's root.
- URLs match the live site one for one: `/book/`, `/podcast/`, `/socials/`, `/blog/`, `/blog/<slug>/`, `/speaking/`, `/more/about/`, `/more/bio/`, `/more/consulting/`, `/more/contact/`.

- `tools/share_cards.py` renders the 21 Open Graph share cards (1200x630) into `site/assets/share/` from the fonts in `tools/fonts/`; needs Pillow. Rerun it when a title changes, then `build.py`.

## Deploy
LIVE at https://prodigalman.com/. The Vercel project `prodigalman` lives in Tim Couet's own Vercel team and is Git-linked to this repo (public, so it works on the Hobby plan): every commit to `main` deploys to production automatically. `vercel.json` sets the output directory to `site`, so no build command runs on Vercel; rebuild locally and commit the result.

```bash
python3 build.py   # canonical and share-image host default to https://prodigalman.com/
git add -A && git commit -m "..." && git push   # Vercel deploys main within about a minute
```

If something else gets deployed over production (a CLI deploy, a test page), either push to `main` again or, in Tim's Vercel dashboard, open the project's Deployments tab and promote the last good Git deployment.

## Open items
- Contact form posts to FormSubmit (`FORM_ENDPOINT` in `build.py`), which emails Tim and redirects to `/thanks/`. Tim must click the one-time activation email that arrives after the first submission; until then nothing is delivered. After activation, FormSubmit shows a random alias that can replace the address in `FORM_ENDPOINT` so it is not visible in the page source.
- Instagram and Facebook embeds were replaced with link cards; YouTube videos play in place through a click-to-load facade.
- Source images in `site/assets/img` were pulled from prodigalman.com/manager/images and cropped. The original YouTube card on the home page linked to a dead `index.php?id=16` page; it now links to the YouTube channel.
