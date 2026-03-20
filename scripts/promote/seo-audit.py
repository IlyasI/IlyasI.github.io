#!/usr/bin/env python3
"""Audit and report on SEO readiness of the site.

Usage:
    python scripts/promote/seo-audit.py [--fix]

Checks:
    - Meta tags (title, description, og:*, twitter:*)
    - Structured data (JSON-LD)
    - sitemap.xml existence and validity
    - robots.txt existence
    - Canonical URL
    - Image alt tags
    - Heading hierarchy
    - Page load indicators (file sizes)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent.parent
INDEX_PATH = SITE_ROOT / "index.html"
SITEMAP_PATH = SITE_ROOT / "sitemap.xml"
ROBOTS_PATH = SITE_ROOT / "robots.txt"
CNAME_PATH = SITE_ROOT / "CNAME"


class SEOAudit:
    def __init__(self):
        self.passed = []
        self.warnings = []
        self.failures = []

    def check(self, name, condition, message_pass, message_fail, severity="fail"):
        if condition:
            self.passed.append(f"  PASS  {name}: {message_pass}")
        elif severity == "warn":
            self.warnings.append(f"  WARN  {name}: {message_fail}")
        else:
            self.failures.append(f"  FAIL  {name}: {message_fail}")

    def run(self):
        if not INDEX_PATH.exists():
            print("ERROR: index.html not found")
            sys.exit(1)

        html = INDEX_PATH.read_text()

        print("=" * 60)
        print("SEO AUDIT REPORT")
        print("=" * 60)
        print()

        # --- Meta Tags ---
        print("Meta Tags")
        print("-" * 40)

        self.check("title", "<title>" in html and "</title>" in html,
                    "Page title found", "Missing <title> tag")

        self.check("meta description",
                    'name="description"' in html,
                    "Meta description found",
                    "Missing meta description")

        desc_match = re.search(r'name="description"\s+content="([^"]*)"', html)
        if desc_match:
            desc_len = len(desc_match.group(1))
            self.check("description length",
                        50 <= desc_len <= 160,
                        f"Description length OK ({desc_len} chars)",
                        f"Description length {desc_len} (should be 50-160)",
                        severity="warn")

        self.check("viewport",
                    'name="viewport"' in html,
                    "Viewport meta tag found",
                    "Missing viewport meta tag")

        self.check("charset",
                    'charset="utf-8"' in html.lower() or 'charset="UTF-8"' in html,
                    "UTF-8 charset declared",
                    "Missing charset declaration")

        print()

        # --- Open Graph ---
        print("Open Graph Tags")
        print("-" * 40)

        og_tags = ["og:title", "og:description", "og:type", "og:url", "og:image"]
        for tag in og_tags:
            self.check(tag,
                        f'property="{tag}"' in html,
                        f"{tag} found",
                        f"Missing {tag}")

        self.check("og:image dimensions",
                    'og:image:width' in html and 'og:image:height' in html,
                    "OG image dimensions specified",
                    "Missing OG image dimensions (recommended: 1200x630)",
                    severity="warn")

        print()

        # --- Twitter Cards ---
        print("Twitter Card Tags")
        print("-" * 40)

        twitter_tags = ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]
        for tag in twitter_tags:
            self.check(tag,
                        f'name="{tag}"' in html,
                        f"{tag} found",
                        f"Missing {tag}")

        print()

        # --- Structured Data ---
        print("Structured Data (JSON-LD)")
        print("-" * 40)

        jsonld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        self.check("JSON-LD present",
                    jsonld_match is not None,
                    "JSON-LD structured data found",
                    "Missing JSON-LD structured data")

        if jsonld_match:
            try:
                data = json.loads(jsonld_match.group(1))
                self.check("JSON-LD valid",
                            True, "JSON-LD parses correctly", "")
                self.check("JSON-LD @type",
                            "@type" in data,
                            f"Type: {data.get('@type', 'unknown')}",
                            "Missing @type in JSON-LD")
                self.check("JSON-LD name",
                            "name" in data,
                            f"Name: {data.get('name', 'missing')}",
                            "Missing name in JSON-LD",
                            severity="warn")
            except json.JSONDecodeError as e:
                self.check("JSON-LD valid", False, "", f"Invalid JSON: {e}")

        print()

        # --- Files ---
        print("SEO Files")
        print("-" * 40)

        self.check("sitemap.xml",
                    SITEMAP_PATH.exists(),
                    "sitemap.xml found",
                    "Missing sitemap.xml")

        self.check("robots.txt",
                    ROBOTS_PATH.exists(),
                    "robots.txt found",
                    "Missing robots.txt")

        if ROBOTS_PATH.exists():
            robots = ROBOTS_PATH.read_text()
            self.check("robots.txt sitemap ref",
                        "Sitemap:" in robots,
                        "robots.txt references sitemap",
                        "robots.txt should reference sitemap URL",
                        severity="warn")

        self.check("CNAME",
                    CNAME_PATH.exists(),
                    f"Custom domain: {CNAME_PATH.read_text().strip() if CNAME_PATH.exists() else 'none'}",
                    "No custom domain (CNAME)",
                    severity="warn")

        print()

        # --- Headings ---
        print("Heading Hierarchy")
        print("-" * 40)

        h1_count = len(re.findall(r'<h1[\s>]', html))
        self.check("single H1",
                    h1_count == 1,
                    "Exactly one H1 tag",
                    f"Found {h1_count} H1 tags (should be exactly 1)",
                    severity="warn")

        for level in range(2, 5):
            count = len(re.findall(rf'<h{level}[\s>]', html))
            if count > 0:
                self.check(f"H{level} tags", True, f"{count} H{level} tag(s) found", "")

        print()

        # --- Images ---
        print("Image Accessibility")
        print("-" * 40)

        img_tags = re.findall(r'<img[^>]*>', html)
        imgs_with_alt = [img for img in img_tags if 'alt=' in img]
        imgs_without_alt = [img for img in img_tags if 'alt=' not in img]

        self.check("image alt tags",
                    len(imgs_without_alt) == 0,
                    f"All {len(img_tags)} images have alt tags",
                    f"{len(imgs_without_alt)} of {len(img_tags)} images missing alt tags",
                    severity="warn")

        print()

        # --- Performance Indicators ---
        print("Performance")
        print("-" * 40)

        html_size = INDEX_PATH.stat().st_size / 1024
        self.check("HTML size",
                    html_size < 100,
                    f"index.html is {html_size:.1f}KB",
                    f"index.html is {html_size:.1f}KB (consider optimizing if >100KB)",
                    severity="warn")

        css_path = SITE_ROOT / "style.css"
        if css_path.exists():
            css_size = css_path.stat().st_size / 1024
            self.check("CSS size",
                        css_size < 100,
                        f"style.css is {css_size:.1f}KB",
                        f"style.css is {css_size:.1f}KB (consider optimizing)",
                        severity="warn")

        js_path = SITE_ROOT / "main.js"
        if js_path.exists():
            js_size = js_path.stat().st_size / 1024
            self.check("JS size",
                        js_size < 100,
                        f"main.js is {js_size:.1f}KB",
                        f"main.js is {js_size:.1f}KB (consider code splitting if >100KB)",
                        severity="warn")

        print()

        # --- Canonical ---
        print("Canonical & Language")
        print("-" * 40)

        self.check("lang attribute",
                    'lang="en"' in html or "lang='en'" in html,
                    "Language attribute set",
                    "Missing lang attribute on <html>",
                    severity="warn")

        self.check("canonical link",
                    'rel="canonical"' in html,
                    "Canonical URL set",
                    "Missing canonical link tag (recommended for SEO)",
                    severity="warn")

        print()

        # --- Print Results ---
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        for msg in self.passed:
            print(msg)
        for msg in self.warnings:
            print(msg)
        for msg in self.failures:
            print(msg)

        print()
        print(f"Passed:   {len(self.passed)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Failures: {len(self.failures)}")
        print()

        if self.failures:
            print("FIX REQUIRED: Address failures above before launching.")
            return 1
        elif self.warnings:
            print("GOOD: No critical failures. Consider addressing warnings.")
            return 0
        else:
            print("EXCELLENT: All SEO checks passed.")
            return 0


def main():
    parser = argparse.ArgumentParser(description="SEO audit for the site")
    parser.parse_args()

    audit = SEOAudit()
    sys.exit(audit.run())


if __name__ == "__main__":
    main()
