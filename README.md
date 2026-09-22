# EGPROC Website

Quarto rebuild of the [EGPROC](https://egproc.org) (European Group of
Process Tracing Studies) website, migrated from its WordPress export.

## Rendering locally

```bash
quarto render
quarto preview
```

## Deployment

Every push to `main` publishes the site to a preview on GitHub Pages:
**https://michaelschulte.github.io/egproc-website/** (egproc.org itself
still serves the WordPress site). The workflow in
`.github/workflows/publish.yml` renders with Quarto and deploys a Pages
artifact; progress shows under the repository's **Actions** tab. The
workflow enables GitHub Pages (source: GitHub Actions) on its first run.

CI renders with the `preview` profile (`_quarto-preview.yml`), which adds a
`noindex` tag to every page so the preview stays out of search results.
When the site moves to egproc.org, drop `--profile preview` from the
workflow and set the custom domain in the repository's Pages settings.

## Updating content

- **Next meeting** — the callout on the home page is hand-written in
  `index.qmd`; update it after each annual meeting.
- **News** — add a `.qmd` file to `news/` with `title` and `date` in its
  front matter; the News page and the home-page cards pick it up.
- **Meetings table** — `meetings/index.qmd` holds a plain HTML table; add a
  row at the top for each new meeting and put its program PDF under
  `files/YYYY/MM/`. (The table is titled "Meetings"; the original WordPress
  page was called "History", recorded in `CONTENT_AUDIT.md`.)

## Changing the design

The design is built around the original EGPROC logo: black geometric
lettering, so the palette is near-black/white with one teal accent.

- **Logo artwork** — `images/brand/`. `egproc-logo.png` is the original
  logo, unchanged; `egproc-mark.png` (no taglines, for the navbar) is a
  crop of just the EGPROC letters from `egproc-logo.png` (taglines removed,
  regenerated during migration); `favicon.png` is the "E" glyph. All are
  black on transparent and are inverted with CSS in dark mode.
- **Colors and fonts** — edit `_brand.yml`. Colours have light and dark
  variants; fonts are Google Fonts (Inter for text, Outfit for headings).
- **Per-mode palette** — `styles-light.scss` / `styles-dark.scss` set the
  navbar, footer, card and border colours. Their hex values mirror
  `_brand.yml`, so change both together.
- **Layout and components** — `styles.scss` holds the shared rules.
- **Base theme** — the `theme:` key in `_quarto.yml` layers
  `cosmo` → `brand` → palette file → `styles.scss`. Keep `brand` in the
  list: without it the Bootswatch theme's colours and fonts override
  `_brand.yml`.

## Content provenance

Content was migrated from a WordPress export (All-in-One WP Migration
bundle) using the one-time scripts in `tools/`. The site renders only
`*.qmd` files; `CONTENT_AUDIT.md` and `README.md` are repository
documentation and are not part of the published site. See
`docs/superpowers/specs/2026-09-22-egproc-website-migration-design.md` for
the migration design and `CONTENT_AUDIT.md` for exactly what was dropped or
changed during migration and why. The `tools/` scripts are kept for
provenance but won't run again without the original export and its scratch
database import.
