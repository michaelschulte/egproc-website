import tempfile
import unittest
from pathlib import Path

from rewrite import (
    parse_meetings, render_meetings_table, rewrite_attachment_links,
    rewrite_internal_links, rewrite_wp_uploads_links, strip_gutenberg,
    unwrap_safelinks,
)


class TestStripGutenberg(unittest.TestCase):
    def test_removes_block_comments_and_empty_paragraphs(self):
        content = (
            "<!-- wp:paragraph -->\n<p>Hello</p>\n<!-- /wp:paragraph -->\n\n"
            "<!-- wp:paragraph -->\n<p></p>\n<!-- /wp:paragraph -->\n\n"
            '<!-- wp:image {"id":904,"sizeSlug":"large"} -->\n'
            '<figure class="wp-block-image"><img src="x.png"/></figure>\n'
            "<!-- /wp:image -->"
        )
        result = strip_gutenberg(content)
        self.assertNotIn("wp:", result)
        self.assertNotIn("<p></p>", result)
        self.assertIn("<p>Hello</p>", result)
        self.assertIn("<figure", result)
        self.assertNotIn("\n\n\n", result)

    def test_unwraps_wp_html_block_and_trailing_nbsp(self):
        content = "<!-- wp:html -->\n<p>Text</p>\n<!-- /wp:html -->\n\n&nbsp;\n"
        self.assertEqual(strip_gutenberg(content), "<p>Text</p>")

    def test_keeps_blank_lines_between_classic_paragraphs(self):
        # Classic-editor posts rely on blank lines for paragraph breaks
        # (Markdown semantics once in Quarto); they must survive.
        content = "Dear EGPROCers,\n\nSee you there!\n\nMichael &amp; Jana"
        self.assertEqual(strip_gutenberg(content), content)


class TestUnwrapSafelinks(unittest.TestCase):
    def test_replaces_wrapped_url_with_target(self):
        content = (
            '<a href="https://eur04.safelinks.protection.outlook.com/?url='
            "https%3A%2F%2Fforms.gle%2FFKReHCd433Ribk2v9&amp;data=04%7C01%7Cx"
            '&amp;reserved=0" target="_blank">https://forms.gle/FKReHCd433Ribk2v9</a>'
        )
        result = unwrap_safelinks(content)
        self.assertIn('href="https://forms.gle/FKReHCd433Ribk2v9"', result)
        self.assertNotIn("safelinks", result)

    def test_leaves_other_links_alone(self):
        content = '<a href="https://www.jads.nl/">JADS</a>'
        self.assertEqual(unwrap_safelinks(content), content)


class TestLinkRewrites(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.uploads_root = Path(self.tmp.name) / "uploads"
        self.images_out = Path(self.tmp.name) / "images"
        self.files_out = Path(self.tmp.name) / "files"

    def tearDown(self):
        self.tmp.cleanup()

    def _make_upload(self, rel_path, size=1000):
        p = self.uploads_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)

    def test_uploads_links_on_any_host_become_local(self):
        self._make_upload("2024/08/Program2024.pdf")
        for host in ("http://egproc.org", "https://egproc.org", "http://eadm.abcde.biz"):
            with self.subTest(host=host):
                content = f'<a href="{host}/wp-content/uploads/2024/08/Program2024.pdf">Program</a>'
                result = rewrite_wp_uploads_links(
                    content, self.uploads_root, self.images_out, self.files_out)
                self.assertEqual(result, '<a href="/files/2024/08/Program2024.pdf">Program</a>')

    def test_thumbnail_reference_resolves_to_largest_rendition(self):
        self._make_upload("2025/06/EGPROC2025_Day1-1024x891.png", size=100)
        self._make_upload("2025/06/EGPROC2025_Day1.png", size=5000)
        content = '<img src="https://egproc.org/wp-content/uploads/2025/06/EGPROC2025_Day1-1024x891.png"/>'
        result = rewrite_wp_uploads_links(
            content, self.uploads_root, self.images_out, self.files_out)
        self.assertEqual(result, '<img src="/images/2025/06/EGPROC2025_Day1.png"/>')

    def test_unresolved_upload_is_left_untouched(self):
        content = '<img src="http://egproc.org/wp-content/uploads/2099/01/gone.jpg">'
        result = rewrite_wp_uploads_links(
            content, self.uploads_root, self.images_out, self.files_out)
        self.assertEqual(result, content)

    def test_attachment_permalink_resolves_by_id(self):
        self._make_upload("2009/04/egproc-2009-fribourg.pdf")
        content = ('<a href="http://www.egproc.org/egproc-2009-fribourg/" '
                   'rel="attachment wp-att-38">Program</a>')
        result = rewrite_attachment_links(
            content, {38: "2009/04/egproc-2009-fribourg.pdf"},
            self.uploads_root, self.images_out, self.files_out)
        self.assertEqual(result, '<a href="/files/2009/04/egproc-2009-fribourg.pdf">Program</a>')

    def test_dated_permalink_to_known_post_becomes_internal(self):
        slug_to_path = {"egproc-2025-comes-to-an-end": "news/egproc-2025-comes-to-an-end"}
        content = '<a href="https://egproc.org/2025/06/28/egproc-2025-comes-to-an-end/">Program</a>'
        result = rewrite_internal_links(content, slug_to_path)
        self.assertEqual(result, '<a href="/news/egproc-2025-comes-to-an-end.qmd">Program</a>')

    def test_unknown_internal_slug_is_left_untouched(self):
        content = '<a href="https://egproc.org/2010/01/01/unknown/">x</a>'
        self.assertEqual(rewrite_internal_links(content, {}), content)


HISTORY = """This is the complete list of EGPROC conferences over the years.
A map of all these places can be found <a href="http://maps.example/">here</a>.

2025 Den Bosch, The Netherlands, <a href="/news/x.qmd">Program</a> (<a href="https://a">Matej Hrkalovic</a>, <a href="https://b">Willemsen, </a><a href="https://c">Krefeld-Schwalb</a>)

2020/21 Tilburg, The Netherlands, <a href="/files/2021/06/Program2021.pdf">Program</a> (Rahal)

2019 Dresden, Germany, <a href="/files/2019/06/Program2019.pdf">Program</a>  (Scherbaum)

2010 Wroclaw, Poland (Zaleskiewicz)

1982 Gothenburg, Sweden (Svenson, Montgomery)
"""


class TestMeetings(unittest.TestCase):
    def test_parse_extracts_every_conference_line(self):
        rows = parse_meetings(HISTORY)
        self.assertEqual([r["year"] for r in rows], ["2025", "2020/21", "2019", "2010", "1982"])
        self.assertEqual(rows[0]["place"], "Den Bosch, The Netherlands")
        self.assertEqual(rows[0]["program"], '<a href="/news/x.qmd">Program</a>')
        self.assertTrue(rows[0]["organisers"].startswith('<a href="https://a">Matej Hrkalovic</a>'))
        self.assertEqual(rows[1]["place"], "Tilburg, The Netherlands")
        self.assertEqual(rows[2]["organisers"], "Scherbaum")
        self.assertEqual(rows[3]["program"], "")
        self.assertEqual(rows[3]["organisers"], "Zaleskiewicz")

    def test_parse_raises_on_unparseable_conference_line(self):
        with self.assertRaises(ValueError):
            parse_meetings("2011 Greifswald Germany Hiemisch\n")

    def test_render_makes_a_classed_table_with_one_row_per_meeting(self):
        html = render_meetings_table(parse_meetings(HISTORY))
        self.assertTrue(html.startswith('<table class="egproc-meetings">'))
        self.assertEqual(html.count("<tr>"), 6)  # header + 5 rows
        self.assertIn("<td>2020/21</td>", html)
        self.assertIn('<td><a href="/files/2019/06/Program2019.pdf">PDF</a></td>', html)
        self.assertIn("<td>Zaleskiewicz</td>", html)


if __name__ == "__main__":
    unittest.main()
