"""Pure content rewrites applied to migrated WordPress content: Gutenberg
block-comment stripping, Outlook safelinks unwrapping, link and media
rewriting, and turning the History page's line-per-conference text into
a table.
"""

import html
import re
from urllib.parse import unquote

from media import copy_and_get_url

_GUTENBERG_COMMENT_RE = re.compile(r"[ \t]*<!--\s*/?wp:[^>]*-->[ \t]*\n?")
_EMPTY_P_RE = re.compile(r"<p>\s*</p>\n?")
# Requires at least one &nbsp;: a pattern that also matched empty lines
# would delete the blank lines that separate classic-editor paragraphs.
_NBSP_LINE_RE = re.compile(r"^[ \t]*(?:&nbsp;[ \t]*)+$\n?", re.MULTILINE)

_SAFELINK_RE = re.compile(
    r"https?://[a-z0-9.]+\.safelinks\.protection\.outlook\.com/\?url=([^&\"']+)[^\"']*"
)

# The host prefix matches ANY scheme://host: the export links program PDFs
# on the dead old host eadm.abcde.biz as well as egproc.org.
_WP_UPLOAD_RE = re.compile(
    r"(?:https?://[^/\"'\s]+)?/wp-content/uploads/(\d{4}/\d{2}/[^\"'\s)>]+)"
)
_ATTACHMENT_LINK_RE = re.compile(r'<a\s+href="[^"]*"\s*rel="attachment wp-att-(\d+)"')
# Permalinks are /YYYY/MM/DD/slug/ for posts and /slug/ for pages.
_INTERNAL_LINK_RE = re.compile(
    r'href="https?://(?:www\.)?egproc\.org/(?:\d{4}/\d{2}/\d{2}/)?([a-zA-Z0-9\-_]+)/?"'
)

_MEETING_LINE_RE = re.compile(
    r"^(?P<year>\d{4}(?:/\d{2})?)\s+"
    r"(?P<place>.+?)"
    r"(?:,\s*(?P<program><a\b[^>]*>Program</a>))?"
    r"\s*\((?P<organisers>.*)\)\s*$"
)


def strip_gutenberg(content):
    """Remove Gutenberg <!-- wp:* --> comments, empty <p></p> blocks and
    &nbsp;-only lines, and collapse the resulting blank-line runs."""
    content = _GUTENBERG_COMMENT_RE.sub("", content)
    content = _EMPTY_P_RE.sub("", content)
    content = _NBSP_LINE_RE.sub("", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def unwrap_safelinks(content):
    """Replace Outlook safelinks wrappers with the URL they wrap."""
    return _SAFELINK_RE.sub(lambda m: unquote(html.unescape(m.group(1))), content)


def rewrite_wp_uploads_links(content, uploads_root, images_out, files_out):
    """Rewrite every /wp-content/uploads/... reference to a copied local
    file; unresolvable references are left untouched."""

    def replace(match):
        url = copy_and_get_url(match.group(1), uploads_root, images_out, files_out)
        return url if url is not None else match.group(0)

    return _WP_UPLOAD_RE.sub(replace, content)


def rewrite_attachment_links(content, attachment_files, uploads_root, images_out, files_out):
    """Rewrite <a href="..." rel="attachment wp-att-NNN"> (pretty attachment
    permalinks) by resolving the attachment id via attachment_files
    (id -> uploads-relative path)."""

    def replace(match):
        rel_path = attachment_files.get(int(match.group(1)))
        if rel_path is None:
            return match.group(0)
        url = copy_and_get_url(rel_path, uploads_root, images_out, files_out)
        return match.group(0) if url is None else f'<a href="{url}"'

    return _ATTACHMENT_LINK_RE.sub(replace, content)


def rewrite_internal_links(content, slug_to_path):
    """Rewrite egproc.org permalinks to migrated items as root-relative
    .qmd links (Quarto resolves those to the rendered page at any depth).
    Unknown slugs stay absolute so they keep working via the live site."""

    def replace(match):
        slug = match.group(1)
        if slug in slug_to_path:
            return f'href="/{slug_to_path[slug]}.qmd"'
        return match.group(0)

    return _INTERNAL_LINK_RE.sub(replace, content)


def parse_meetings(content):
    """Parse the History page's 'YEAR Place, Country, <a>Program</a>
    (Organisers)' lines. Lines not starting with a year are intro text
    and skipped; a year line that doesn't parse raises ValueError so a
    malformed row can't silently vanish."""
    rows = []
    for line in content.splitlines():
        line = line.strip()
        if not re.match(r"^\d{4}", line):
            continue
        match = _MEETING_LINE_RE.match(line)
        if match is None:
            raise ValueError(f"unparseable conference line: {line!r}")
        rows.append({
            "year": match.group("year"),
            "place": match.group("place").strip(),
            "program": match.group("program") or "",
            "organisers": match.group("organisers").strip(),
        })
    return rows


def render_meetings_table(rows):
    """HTML table for the Meetings page. Program links are relabelled by
    target: PDFs say 'PDF', anything else keeps 'Program'."""
    out = ['<table class="egproc-meetings">',
           "<thead><tr><th>Year</th><th>Place</th><th>Organisers</th><th>Program</th></tr></thead>",
           "<tbody>"]
    for r in rows:
        program = r["program"]
        if ".pdf" in program.lower():
            program = program.replace(">Program</a>", ">PDF</a>")
        out.append(f"<tr><td>{r['year']}</td><td>{r['place']}</td>"
                   f"<td>{r['organisers']}</td><td>{program}</td></tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)
