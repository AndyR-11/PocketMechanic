"""Offline tests: never contact Groq, Google, Bing or DDGS during this suite."""
import unittest
from unittest.mock import patch

from app.services import manual_finder as finder


class ManualFinderTests(unittest.TestCase):
    def setUp(self):
        finder._lookup_cached.cache_clear()

    def test_brand_domains_are_dynamic(self):
        for url, make in [
            ("https://assets.sia.toyota.com/pdfs/2025.pdf", "Toyota"),
            ("https://maintenance-schedules.nissanusa.com/2026/altima", "Nissan"),
            ("https://owners.honda.com/manual", "Honda"),
            ("https://www.fordservicecontent.com/Manual.pdf", "Ford"),
            ("https://www.peugeot.com/en/owners", "Peugeot"),
            ("https://www.subaru.com/owners", "Subaru"),
        ]:
            with self.subTest(url=url):
                self.assertTrue(finder._is_approved_brand_domain(url, make))

    def test_fake_brand_domain_is_rejected(self):
        for url in [
            "https://fake-toyota.com/2025/tacoma/maintenance",
            "https://toyota.com.fraud.example/2025/tacoma/maintenance",
            "http://toyota.com/2025/tacoma/maintenance",
            "https://bad@toyota.com/2025/tacoma/maintenance",
        ]:
            with self.subTest(url=url):
                self.assertFalse(finder._is_approved_brand_domain(url, "Toyota"))

    def test_relevance_requires_make_model_year_and_maintenance(self):
        good = finder._score_hit({
            "title": "2026 Nissan Altima Maintenance Schedule",
            "href": "https://maintenance-schedules.nissanusa.com/maintenance-schedules/2026/altima/",
        }, 2026, "Nissan", "Altima")
        self.assertIsNotNone(good)
        self.assertEqual(good["source_type"], "likely_official")
        self.assertIsNone(finder._score_hit({
            "title": "2025 Nissan Altima Maintenance Schedule",
            "href": "https://www.nissanusa.com/2025/altima/maintenance",
        }, 2026, "Nissan", "Altima"))
        self.assertIsNone(finder._score_hit({
            "title": "2026 Nissan Rogue Maintenance Schedule",
            "href": "https://www.nissanusa.com/2026/rogue/maintenance",
        }, 2026, "Nissan", "Altima"))

    def test_general_official_portal_without_model_year_is_labeled(self):
        portal = finder._score_hit({
            "title": "Toyota Tacoma Maintenance Schedule and Owners Manuals",
            "href": "https://www.toyota.com/owners/warranty-owners-manuals/tacoma/",
        }, 2025, "Toyota", "Tacoma")
        self.assertIsNotNone(portal)
        self.assertEqual(portal["source_type"], "manufacturer_portal")
        self.assertIn("choose the correct year", portal["source_label"])

    def test_unverified_blog_not_promoted_as_official(self):
        item = {
            "title": "2019 Peugeot 3008 maintenance schedule",
            "href": "https://randomblog.example/maintenance/2019-peugeot-3008",
        }
        self.assertIsNone(finder._score_hit(item, 2019, "Peugeot", "3008"))

    def test_legitimate_manual_copy_is_labeled_third_party(self):
        value = finder._score_hit({
            "title": "2019 Peugeot 3008 owner's manual",
            "href": "https://www.manualslib.com/manuals/2019-peugeot-3008-maintenance.html"
        }, 2019, "Peugeot", "3008")
        self.assertEqual(value["source_type"], "third_party_copy")

    def test_no_results_returns_aaa_fallback(self):
        with patch.object(finder, "_ddgs_results", return_value=[]), patch.object(finder, "_bing_rss_results", return_value=[]):
            result = finder.find_maintenance_manuals(2007, "Saab", "9-3")
        self.assertEqual(result["manuals"], [])
        self.assertFalse(result["automatic_results_found"])
        self.assertIn("AAA", result["aaa_fallback"]["title"])
        self.assertIn("does NOT mean", result["message"])

    def test_exact_vehicle_found_no_aaa_claim(self):
        results = [{"title": "2025 Toyota Tacoma Maintenance Warranty Guide PDF",
                    "href": "https://assets.sia.toyota.com/publications/en/omms-s/2025-Tacoma-Guide.pdf"}]
        with patch.object(finder, "_ddgs_results", return_value=results), patch.object(finder, "_bing_rss_results", return_value=[]):
            result = finder.find_maintenance_manuals(2025, "Toyota", "Tacoma")
        self.assertTrue(result["automatic_results_found"])
        self.assertEqual(len(result["manuals"]), 1)
        self.assertTrue(result["manuals"][0]["url"].endswith(".pdf"))

    def test_repeated_lookup_reuses_one_hour_cache(self):
        results = [{"title": "2026 Nissan Altima maintenance schedule",
                    "href": "https://maintenance-schedules.nissanusa.com/maintenance-schedules/2026/altima/"}]
        with patch.object(finder, "_ddgs_results", return_value=results) as ddgs, patch.object(finder, "_bing_rss_results", return_value=[]):
            finder.find_maintenance_manuals(2026, "Nissan", "Altima")
            count = ddgs.call_count
            finder.find_maintenance_manuals(2026, "Nissan", "Altima")
            self.assertEqual(ddgs.call_count, count)

    def test_no_specs_or_maintenance_cycles_in_source_data(self):
        with patch.object(finder, "_ddgs_results", return_value=[]), patch.object(finder, "_bing_rss_results", return_value=[]):
            result = finder.find_maintenance_manuals(2016, "Honda", "Civic")
        self.assertNotIn("5000", str(result))
        self.assertNotIn("oil change", str(result).lower())
        self.assertIn("AAA", result["aaa_fallback"]["title"])

    def test_handles_malicious_redirects(self):
        self.assertEqual(finder._unwrap_search_url("https://www.google.com/search?q=toyota"), "")
        self.assertEqual(finder._unwrap_search_url("javascript:alert(1)"), "")


if __name__ == "__main__":
    unittest.main()
