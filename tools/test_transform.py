import tempfile
import unittest
from pathlib import Path

from transform import build_frontmatter, transform_content


class TestFrontmatter(unittest.TestCase):
    def test_posts_get_title_and_date(self):
        item = {"id": 910, "type": "post", "title": "EGPROC 2026",
                "date": "2026-03-19 10:00:00", "slug": "egproc-2026"}
        self.assertEqual(build_frontmatter(item, "news"),
                         '---\ntitle: "EGPROC 2026"\ndate: 2026-03-19\n---')

    def test_pages_get_title_only_and_quotes_are_escaped(self):
        item = {"id": 825, "type": "page", "title": 'Say "hi"', "date": "2009-02-10 00:00:00"}
        self.assertEqual(build_frontmatter(item, "about"), '---\ntitle: "Say \\"hi\\""\n---')


class TestTransformContent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "uploads/2024/08").mkdir(parents=True)
        (root / "uploads/2024/08/Program2024.pdf").write_bytes(b"p")
        self.ctx = {
            "uploads_root": root / "uploads",
            "images_out": root / "images",
            "files_out": root / "files",
            "attachment_files": {},
            "slug_to_path": {"egproc-2026": "news/egproc-2026"},
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_gutenberg_post_is_cleaned_and_links_rewritten(self):
        item = {"id": 878, "type": "post", "content":
                "<!-- wp:paragraph -->\n<p>Program <a href=\"http://egproc.org/wp-content/uploads/2024/08/Program2024.pdf\">here</a>.</p>\n<!-- /wp:paragraph -->"}
        out = transform_content(item, self.ctx)
        self.assertEqual(out, '<p>Program <a href="/files/2024/08/Program2024.pdf">here</a>.</p>')

    def test_meetings_page_becomes_a_table_with_fixes_applied(self):
        item = {"id": 64, "type": "page", "content":
                "Intro line.\n\n1016 Warwik, United Kingdom, Program (Walasek &amp; Mullett)\n\n"
                "2010 Wroclaw, Poland (Zaleskiewicz)\n"}
        out = transform_content(item, self.ctx)
        self.assertTrue(out.startswith("Intro line."))
        self.assertIn('<table class="egproc-meetings">', out)
        self.assertIn("<td>2026</td><td>Warwick, United Kingdom</td>", out)
        self.assertIn('href="/news/egproc-2026.qmd"', out)

    def test_body_override_and_append_are_applied(self):
        item = {"id": 804, "type": "post", "content": "<div>junk</div>"}
        self.assertIn("36th meeting", transform_content(item, self.ctx))
        item = {"id": 825, "type": "page", "content": "About text."}
        out = transform_content(item, self.ctx)
        self.assertTrue(out.startswith("About text.\n\n"))
        self.assertIn("https://eadm.eu", out)


if __name__ == "__main__":
    unittest.main()
