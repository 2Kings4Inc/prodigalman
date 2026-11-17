# Prodigal Man (prodigalman.com rebuild)

Static rebuild of https://prodigalman.com/ (Tim Couet) in the look of foreverchanged.vercel.app.
Built Nov 17, 2026. Not a 2 Kings 4 Inc brand; client work.

- `build.py` generates `site/` from `content/posts.json` (11 blog posts scraped from the live site). No dependencies.
- `python3 build.py` for folder-style links (`/book/`), `python3 build.py --file` for explicit `index.html` links (artifact previews).
- `site/` is committed so it can be deployed as-is. Vercel: output directory `site`, framework none, `vercel.json` at this folder's root.
- URLs match the live site one for one: `/book/`, `/podcast/`, `/socials/`, `/blog/`, `/blog/<slug>/`, `/speaking/`, `/more/about/`, `/more/bio/`, `/more/consulting/`, `/more/contact/`.

- `tools/share_cards.py` renders the 21 Open Graph share cards (1200x630) into `site/assets/share/` from the fonts in `tools/fonts/`; needs Pillow. Rerun it when a title changes, then `build.py`.

## Deploy
LIVE at https://prodigalman.vercel.app. The Vercel project `prodigalman` was transferred to Tim Couet's own Vercel account on Nov 17, 2026, so deploys need a token from Tim's account (saved as a network secret for api.vercel.com on the "Prodigal Man" cloud environment, or in a Mac-only `.vercel-token` file). CLI-only, not Git-linked. Replace the scope below with Tim's team slug:

```bash
python3 build.py   # canonical and share-image host default to https://prodigalman.com/ (live on Vercel since Nov 17, 2026)
rm -rf /tmp/pm-deploy && mkdir /tmp/pm-deploy && cp -r site/. /tmp/pm-deploy/ && cp vercel.json /tmp/pm-deploy/
cd /tmp/pm-deploy && vercel deploy --prod --yes --name prodigalman --scope arv1221-4360s-projects
```

## Open items
- Contact form posts to FormSubmit (`FORM_ENDPOINT` in `build.py`), which emails Tim and redirects to `/thanks/`. Tim must click the one-time activation email that arrives after the first submission; until then nothing is delivered. After activation, FormSubmit shows a random alias that can replace the address in `FORM_ENDPOINT` so it is not visible in the page source.
- Instagram and Facebook embeds were replaced with link cards; YouTube videos play in place through a click-to-load facade.
- Source images in `site/assets/img` were pulled from prodigalman.com/manager/images and cropped. The original YouTube card on the home page linked to a dead `index.php?id=16` page; it now links to the YouTube channel.
