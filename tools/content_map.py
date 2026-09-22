"""The curated content plan: which WordPress items are kept, where each
one lands in the Quarto site, and the per-item text fixes recorded in the
design spec (docs/superpowers/specs/2026-09-22-...). Every curation
decision lives here so CONTENT_AUDIT.md can be generated from it.
"""

MEETINGS_PAGE_ID = 64

# WordPress id -> reason it was dropped (surfaced in CONTENT_AUDIT.md).
DROP_IDS = {
    2: "WordPress default German sample page (Beispiel-Seite).",
    18: "Gallery: body is only a NextGEN [album=1,extend] shortcode; the "
        "plugin and its images are not in the export, so there is nothing to show.",
    772: "Empty 'News' page that only served as WordPress's posts-page "
         "placeholder; replaced by the Quarto news listing.",
    1: "WordPress default 'Hallo Welt!' post.",
    4: "One-line date test post ('Test des Datums.').",
}

# Kept pages: WordPress id -> (section directory, filename without .qmd).
PAGE_TARGETS = {
    825: ("about", "index"),
    3: ("mailing-list", "index"),
    MEETINGS_PAGE_ID: ("meetings", "index"),
}


def resolve_target(item):
    """(section, filename) for a kept item, None for a dropped one.

    Raises KeyError for a page that is in neither list, so an
    unclassified page is a loud failure rather than a silent loss.
    """
    id_ = item["id"]
    if id_ in DROP_IDS:
        return None
    if item["type"] == "page":
        return PAGE_TARGETS[id_]
    return ("news", item["slug"])


# Literal (old, new) replacements applied after link rewriting. Each one is
# listed in CONTENT_AUDIT.md.
TEXT_FIXES = {
    MEETINGS_PAGE_ID: [
        (
            "1016 Warwik, United Kingdom, Program (Walasek &amp; Mullett)",
            '2026 Warwick, United Kingdom, <a href="/news/egproc-2026.qmd">Program</a> '
            "(Walasek &amp; Mullett)",
        ),
    ],
    # The "Dates are out" post ends with a bare Vimeo URL that WordPress
    # auto-embedded; Quarto would show it as plain text.
    788: [
        ("https://vimeo.com/105023242",
         '<a href="https://vimeo.com/105023242">Video: Galway (Vimeo)</a>'),
    ],
    # The 2017 poster image had an empty alt.
    793: [('alt=""', 'alt="EGPROC 2017 poster"')],
}

# Whole-body replacements for items whose stored markup is unsalvageable.
BODY_OVERRIDES = {
    # Pasted from Gmail: inline styles, gmail-* spans, &nbsp; spacer divs.
    # Wording is unchanged; only markup was removed.
    804: """The **36th meeting of the European Group of Process Tracing Studies (EGPROC)** will take place in **Galway, Ireland** from the **22nd to the 24th of June 2017** and we are delighted to announce two special guests: Prof. Neil Stewart of Warwick University, and Dr. KongFatt Wong-Lin of Ulster University.

Due to numerous requests, **the deadline for abstract submission has been extended until the 30th of April**.

If you have not done so already, we invite you to submit your abstract through the conference website: <http://tiny.cc/egproc2017>

Please share this information with other researchers who might be interested in the topic.

We look forward to having you in Galway, Ireland.

*EGPROC 2017 organizing committee:*
Denis O'Hora (<denis.ohora@nuigalway.ie>),
Arkady Zgonnikov (<arkady.zgonnikov@nuigalway.ie>),
Avril Hand (<a.hand1@nuigalway.ie>),
Santi Garcia (<s.garciaguerrero1@nuigalway.ie>)
""",
}

# Text appended to an item's body (a blank line is inserted before it).
APPEND = {
    825: "EGPROC is closely associated with the "
         "[European Association for Decision Making (EADM)](https://eadm.eu), "
         "whose members make up most of the group.",
}
