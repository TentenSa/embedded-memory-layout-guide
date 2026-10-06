"""Offline check that relative links in markdown files point at files that exist."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s]+)\)")


class LinkTests(unittest.TestCase):
    def test_relative_links_resolve(self):
        missing = []
        for md in ROOT.rglob("*.md"):
            if ".git" in md.parts:
                continue
            for target in LINK.findall(md.read_text(encoding="utf-8")):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                path = target.split("#", 1)[0]
                if path and not (md.parent / path).exists():
                    missing.append(f"{md.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [], "broken relative links")


if __name__ == "__main__":
    unittest.main()
