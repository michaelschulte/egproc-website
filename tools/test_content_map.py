import unittest

from content_map import (
    APPEND, BODY_OVERRIDES, DROP_IDS, MEETINGS_PAGE_ID, TEXT_FIXES, resolve_target,
)


def page(id_, slug):
    return {"id": id_, "type": "page", "slug": slug, "title": slug}


def post(id_, slug):
    return {"id": id_, "type": "post", "slug": slug, "title": slug}


class TestResolveTarget(unittest.TestCase):
    def test_kept_pages_map_to_their_sections(self):
        self.assertEqual(resolve_target(page(825, "about")), ("about", "index"))
        self.assertEqual(resolve_target(page(3, "mailing-list")), ("mailing-list", "index"))
        self.assertEqual(resolve_target(page(64, "programs-and-information-on-egproc-conferences")),
                         ("meetings", "index"))

    def test_dropped_pages_and_posts_return_none(self):
        for id_, slug in [(2, "beispiel-seite"), (18, "gallery"), (772, "news")]:
            self.assertIsNone(resolve_target(page(id_, slug)), slug)
        for id_, slug in [(1, "hallo-welt"), (4, "test"), (827, "egproc-2020-in-tilburg")]:
            self.assertIsNone(resolve_target(post(id_, slug)), slug)

    def test_every_drop_has_a_reason(self):
        for id_, reason in DROP_IDS.items():
            self.assertTrue(reason.strip(), f"id {id_} has no reason")

    def test_posts_land_in_news_by_slug(self):
        self.assertEqual(resolve_target(post(910, "egproc-2026")), ("news", "egproc-2026"))
        self.assertEqual(resolve_target(post(826, "hello-world")), ("news", "hello-world"))

    def test_unknown_page_is_dropped_loudly(self):
        # A page we never classified must not silently land somewhere.
        with self.assertRaises(KeyError):
            resolve_target(page(9999, "mystery"))


class TestFixes(unittest.TestCase):
    def test_meetings_page_fixes_the_2026_row(self):
        old, new = TEXT_FIXES[MEETINGS_PAGE_ID][0]
        self.assertIn("1016 Warwik", old)
        self.assertIn("2026 Warwick", new)
        self.assertIn('href="/news/egproc-2026.qmd"', new)

    def test_galway_post_has_a_plain_text_override(self):
        body = BODY_OVERRIDES[804]
        self.assertNotIn("gmail-", body)
        self.assertNotIn("style=", body)
        self.assertIn("30th of April", body)
        self.assertIn("denis.ohora@nuigalway.ie", body)

    def test_about_gets_the_eadm_line(self):
        self.assertIn("https://eadm.eu", APPEND[825])


if __name__ == "__main__":
    unittest.main()
