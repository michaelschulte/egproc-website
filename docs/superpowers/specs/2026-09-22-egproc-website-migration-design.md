# EGPROC Website: WordPress → Quarto Migration

- **Date:** 2026-09-22
- **Status:** Approved
- **Source:** WordPress export at `/Users/michael/git_stuff/wp_egproc/egproc-org-20260922-113210-8q9p1q94pb7l/` (All-in-One WP Migration `.wpress` bundle for https://egproc.org, WordPress 6.9.8, theme `twentynineteen`, table prefix `egproc_`)
- **Target:** New standalone Quarto website project at `/Users/michael/git_stuff/egproc-website/`, pushed to a new public GitHub repo `michaelschulte/egproc-website` (branch `main`) and deployed to GitHub Pages as a `noindex` preview
- **Sibling project:** `/Users/michael/git_stuff/eadm-website/` — the same migration was done there first; this project reuses its stack and conventions

## 1. Goal

Rebuild the public content of the EGPROC (European Group of Process Tracing
Studies) WordPress site as a static Quarto website with a modern, responsive,
easily re-skinnable design. The site is tiny (a handful of pages, ~22 news
posts, 20 program PDFs), so the migration favours a curated result over a
1:1 copy of the WordPress structure.

## 2. Source data

The export was unpacked with a throwaway script and its `database.sql`
imported into a scratch MariaDB 10.11 Docker container `egproc_mysql_import`
(database `egproc`, `utf8mb4`, prefix rewritten from `SERVMASK_PREFIX_` to
`egproc_`). The container is migration scaffolding only and is removed once
content extraction is done.

Inventory from the imported DB:

| post_type | status | count | notes |
|---|---|---|---|
| page | publish | 6 | About, Mailing List, Gallery, History, News, Beispiel-Seite |
| page | draft | 1 | "Process Tracing Literature", empty |
| post | publish | 25 | 22 conference announcements 2009–2026 + 3 stubs |
| attachment | inherit | 30 | 20 PDFs, 10 images |
| nav_menu_item | publish | 3 | About · Mailing List · History |

Site options: `show_on_front = posts` (homepage was a raw post feed),
permalinks `/%year%/%monthnum%/%day%/%postname%/`, tagline "Process tracing
is our thing".

`uploads/` is 36MB (83 files, of which 33 are original renditions; the rest
are WordPress thumbnail sizes).

## 3. Content scope and curation

**Kept**

- Pages: About (825), Mailing List (3), History (64).
- Posts: all 22 conference-related posts, plus "New EGPROC Site" (826, 2009)
  which is genuine site history.

**Dropped** (each recorded in `CONTENT_AUDIT.md`)

- Gallery (18): body is a `[album=1,extend]` NextGEN shortcode; the plugin
  and its gallery images are not in the export, so there is nothing to show.
- News (772): empty page used only as a WordPress posts-page placeholder;
  replaced by the Quarto listing.
- Beispiel-Seite (2): WordPress default German sample page.
- Draft "Process Tracing Literature" (90): never published, empty.
- "Hallo Welt!" (1) and "Test" (4): WordPress default post and a date test.

**Content fixes** (each recorded in `CONTENT_AUDIT.md` with before/after)

- History: `1016 Warwik, United Kingdom` → `2026 Warwick, United Kingdom`;
  its Program entry links to the EGPROC 2026 post (there is no program yet).
- Program links pointing at the dead old host `eadm.abcde.biz` and at
  `egproc.org/wp-content/uploads/...` are rewritten to the vendored PDFs in
  `files/`. The 2009 Fribourg "Program" link points at a WordPress
  attachment page; it is rewritten to the PDF itself
  (`2009/04/egproc-2009-fribourg.pdf`).
- The 2025 History row's Program link (to the "EGPROC 2025 comes to an end"
  post) becomes an internal link to that post.
- The 2022 Amsterdam post's Outlook safelinks-wrapped URLs are unwrapped to
  the real targets (`forms.gle/...`, `neuroeconomist.net/egproc`).
- The 2017 "deadline extended" post's pasted Gmail markup (inline styles,
  `gmail-*` spans, `<div>&nbsp;</div>` spacers) is reduced to plain
  paragraphs; wording unchanged.
- The 2017 "Abstract submission" post's poster image
  (`EGPROC17-212x300.png` from the dead host) is replaced by the local
  full-size `EGPROC17.png`.
- The 2017 "Dates are out" post's bare `https://vimeo.com/...` line (a WP
  auto-embed) becomes an explicit link.
- Obvious WordPress cruft is stripped: Gutenberg `<!-- wp:* -->` comments,
  empty `<p></p>` blocks, trailing `&nbsp;` paragraphs.

## 4. Information architecture

```
/                 Home: logo hero, "Next meeting" callout (EGPROC 2026,
                  Warwick, 16–17 July 2026), About text, 3 latest news cards,
                  link cards to Meetings / News / Mailing list
/about/           About page + one line placing EGPROC in the EADM community
                  (link to eadm.eu)
/meetings/        History content rendered as a table:
                  Year · Place · Organisers · Program (PDF or post link)
/news/            Quarto listing of the 23 posts, newest first, dated
/news/<slug>.qmd  one post each (slug = WordPress post_name)
/mailing-list/    Mailing List page
/files/YYYY/MM/   vendored PDFs, mirroring the uploads layout
/images/YYYY/MM/  images referenced by kept content, largest rendition only
/images/brand/    logo artwork for navbar, hero and favicon
```

Navbar: logo (links home) · About · Meetings · News · Mailing List, plus the
light/dark toggle; collapses to a hamburger below `lg`. Footer: "EGPROC —
European Group of Process Tracing Studies" · Mailing List · link to eadm.eu.

The "Next meeting" callout on the home page is hand-maintained content in
`index.qmd` (it is the one thing that changes yearly), not derived from the
listing.

## 5. Content pipeline

One-time scripts under `tools/` (kept for provenance, not part of the served
site), following the eadm layout:

1. `extract.py` — queries the scratch MariaDB via
   `JSON_ARRAYAGG(JSON_OBJECT(...))` with `mysql -r`, writing
   `tools/_extracted/{pages,posts,categories,attachments}.json`
   (gitignored).
2. `content_map.py` — the curated keep/drop list and slug → output path map
   from §3–4; the single place where curation decisions live.
3. `rewrite.py` — pure functions, unit-tested: strip Gutenberg comments and
   empty blocks, unwrap safelinks, rewrite internal links and
   `wp-content/uploads` references to local paths, apply the per-item text
   fixes from §3.
4. `media.py` — copy all 20 PDFs to `files/` (listed as a Quarto `resources`
   entry so unreferenced ones still deploy) and the largest rendition of
   each referenced image to `images/`, dropping thumbnail sizes.
5. `transform.py` — orchestrates: emits one `.qmd` per kept item with YAML
   front matter (`title`; posts also `date`), builds the Meetings table from
   the History page's line-per-conference text, and writes
   `CONTENT_AUDIT.md`.
6. `check_links.py` — walks `_site/` after render and fails on any broken
   internal link or missing local file.

Post bodies: older posts are classic-editor blank-line-separated text with
inline HTML; newer ones are Gutenberg blocks. After stripping block comments
both forms are valid Markdown with embedded raw HTML, which Quarto passes
through, so no HTML→Markdown conversion is needed (same finding as eadm).

## 6. Design

Quarto `website` project, `cosmo` Bootswatch base layered with `_brand.yml`,
a per-mode palette file and one shared `styles.scss` — identical layering to
eadm so the two sites are maintained the same way.

- **Brand:** the logo is pure black geometric lettering. Palette: near-black
  ink `#1d1d1f` / white, warm gray surfaces, and a single accent — deep teal
  `#0f6e6e` (light) / `#5cc8c8` (dark) — for links, buttons and the active
  nav item. Deliberately distinct from EADM's red.
- **Type:** Inter (body), Outfit (headings; geometric, echoing the logo).
- **Logo artwork** in `images/brand/`: `egproc-logo.png` (= `EGPROC_1.png`,
  full, hero), `egproc-mark.png` (= `cropped-EGPROC_1.png`, navbar; inverted
  with a CSS filter in dark mode), `favicon.png` cropped from the "E".
- **Responsive:** hamburger below `lg`; card grids 3 → 2 → 1 columns; the
  meetings table scrolls horizontally on narrow screens; hero logo scales
  with viewport width.
- **Light/dark** toggle in the navbar via Quarto's theme pair.

Changing the design = edit `_brand.yml` (colours/fonts) and the two palette
files; documented in `README.md`.

## 7. Repository layout

```
egproc-website/
├── _quarto.yml, _quarto-preview.yml, _brand.yml
├── styles.scss, styles-light.scss, styles-dark.scss
├── index.qmd
├── about/index.qmd
├── meetings/index.qmd
├── news/index.qmd + news/<slug>.qmd × 23
├── mailing-list/index.qmd
├── images/{brand,YYYY/MM}/
├── files/YYYY/MM/*.pdf
├── tools/                 (extract, content_map, rewrite, media, transform,
│                           check_links + tests; _extracted/ gitignored)
├── docs/superpowers/      (this spec + plan; excluded from render)
├── .github/workflows/publish.yml
├── CONTENT_AUDIT.md, README.md, .gitignore
```

## 8. Git, GitHub, deployment

- `git init` in `egproc-website/`; the export lives in the sibling
  `wp_egproc/` and never enters git.
- Public repo `michaelschulte/egproc-website` created with `gh`, branch
  `main`, initial history pushed.
- `publish.yml` as in eadm: on push to `main`, set up Quarto 1.9.37, render
  with `--profile preview` (adds `<meta name="robots" content="noindex">`),
  deploy a Pages artifact to `https://michaelschulte.github.io/egproc-website/`.
  `egproc.org` keeps serving WordPress until DNS is switched; at that point
  drop the profile flag and set the custom domain.

## 9. Verification

- `quarto render` completes without warnings about missing files.
- `tools/check_links.py` passes on `_site/`.
- Every kept page/post from §3 exists as a `.qmd`; all 20 PDFs exist in
  `files/` and every Meetings row that had a program link has one that
  resolves.
- Rendered site checked in the browser at desktop and phone widths, light
  and dark.
- Pages workflow run succeeds and the preview URL serves the site.
