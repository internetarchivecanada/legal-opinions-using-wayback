import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build"))

from classify import classify  # noqa: E402
from wayback_urls import find  # noqa: E402


class WaybackUrls(unittest.TestCase):
    # Each of these came from archive.org's OCR of a real RECAP filing.
    def test_clean_url(self):
        (m,) = find("see https://web.archive.org/web/20230405080036/https://abcnews.go.com/x.")
        self.assertEqual(m["timestamp"], "20230405080036")
        self.assertEqual(m["target"], "https://abcnews.go.com/x")

    def test_spaced_host_and_typo_scheme(self):
        (m,) = find("found at: httos://web. archive. org/web/20060523010301/http://s- doc.com/medi")
        self.assertEqual(m["timestamp"], "20060523010301")
        self.assertTrue(m["target"].startswith("http://s-"))

    def test_split_timestamp(self):
        (m,) = find("https://web archive .org/web/20220730 14343 1 /http://nanoheal.com/")
        self.assertEqual(m["timestamp"], "20220730143431")
        self.assertEqual(m["target"], "http://nanoheal.com/")

    def test_collapsed_scheme_slash(self):
        (m,) = find("web.archive.org/web/2019/https:/example.com/a")
        self.assertEqual(m["target"], "https://example.com/a")

    def test_repeated_header_counted_once(self):
        page = "web.archive.org/web/20220516193956/https://example.com/ Page 1 "
        (m,) = find(page * 3)
        self.assertEqual(m["count"], 3)

    def test_plain_mention_is_not_a_url(self):
        self.assertEqual(find("archived by the Wayback Machine at web.archive.org"), [])


class Classify(unittest.TestCase):
    def test_court(self):
        self.assertEqual(classify("MEMORANDUM OPINION AND ORDER"), ("court", "opinion"))
        self.assertEqual(classify("ORDER granting 12 Motion to Dismiss"), ("court", "order"))
        self.assertEqual(classify("REPORT AND RECOMMENDATIONS re 40 MOTION"), ("court", "recommendation"))

    def test_party(self):
        self.assertEqual(classify("MEMORANDUM in Opposition re 12 MOTION to Dismiss"), ("party", "argument"))
        self.assertEqual(classify("MOTION for Preliminary Injunction"), ("party", "motion"))
        self.assertEqual(classify("DECLARATION of Jane Doe in Support"), ("party", "declaration"))
        self.assertEqual(classify("COMPLAINT against Acme Corp."), ("party", "pleading"))

    def test_attachments_read_their_own_short_description(self):
        entry = "MOTION for Default Judgment, filed by Plaintiff Bungie Inc. (Attachments: # 1 Exhibit A)"
        self.assertEqual(classify(entry, 1, "Exhibit A"), ("party", "exhibit"))
        self.assertEqual(classify(entry, 3, "Screenshots of website"), ("party", "exhibit"))
        self.assertEqual(classify(entry, 2, "Affidavit of Internet Archive"), ("party", "declaration"))
        self.assertEqual(classify(entry, 4, None), ("party", "exhibit"))

    # Main-document descriptions from the first page of a live RECAP search,
    # 2026-10-19. The attachment list once made every one of these an exhibit.
    def test_live_descriptions(self):
        cases = [
            ("Response Filed by Lynn H. Butler for Creditor Husch Blackwell LP (Attachments: # 1 Exhibit A)", "argument"),
            ("AFFIDAVIT/DECLARATION of Chelsea Papciak in Support re 29 MOTION for Judgment (Attachments: # 1 Exhibit)", "declaration"),
            ("MOTION to Strike and Memorandum in Support filed by Counter Claimant (Attachments: # 1 Exhibit)", "motion"),
            ("DECLARATION of Kenneth M. Trujillo-Jamison in Support re: 16 MOTION to Dismiss", "declaration"),
            ("NOTICE of Request For Judicial Notice re: 16 MOTION to Dismiss the Amended Complaint", "motion"),
            ("MOTION for Default Judgment, filed by Plaintiff Bungie Inc. (Attachments: # 1 Exhibit A)", "motion"),
        ]
        for description, kind in cases:
            with self.subTest(description=description):
                self.assertEqual(classify(description), ("party", kind))

    def test_unmatched_is_kept(self):
        self.assertEqual(classify("NOTICE of Appearance"), ("unknown", "other"))
        self.assertEqual(classify(""), ("unknown", "other"))


if __name__ == "__main__":
    unittest.main()
