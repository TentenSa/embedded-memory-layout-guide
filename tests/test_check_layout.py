import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_layout as cl  # noqa: E402

EX = ROOT / "examples" / "dualcore-baseline"

MAP_HEADER = """Memory Configuration

Name             Origin             Length             Attributes
RAM              0x0000000020000000 0x0000000000001000 xrw
*default*        0x0000000000000000 0xffffffffffffffff

Linker script and memory map

"""


def run(map_text, config):
    regions, sections = cl.parse_map(map_text)
    return cl.check(regions, sections, config)


class ParseTests(unittest.TestCase):
    def test_regions_and_sections(self):
        text = MAP_HEADER + ".data           0x0000000020000000      0x100\n"
        regions, sections = cl.parse_map(text)
        self.assertEqual([r.name for r in regions], ["RAM"])
        self.assertEqual(regions[0].length, 0x1000)
        self.assertEqual(sections, [cl.Section(".data", 0x20000000, 0x100)])

    def test_long_section_name_on_its_own_line(self):
        text = (
            MAP_HEADER
            + ".a_very_long_output_section_name_that_wraps\n"
            + "                0x0000000020000100       0x40\n"
        )
        _, sections = cl.parse_map(text)
        self.assertEqual(sections[0].addr, 0x20000100)
        self.assertEqual(sections[0].size, 0x40)

    def test_default_region_is_ignored(self):
        regions, _ = cl.parse_map(MAP_HEADER)
        self.assertNotIn("*default*", [r.name for r in regions])


class CheckTests(unittest.TestCase):
    def test_match_passes(self):
        text = MAP_HEADER + ".stack         0x0000000020000000      0x400\n"
        errors, _, _ = run(text, {"expect": [{"section": ".stack", "size": 1024}]})
        self.assertEqual(errors, [])

    def test_size_mismatch_is_error(self):
        text = MAP_HEADER + ".stack         0x0000000020000000      0x200\n"
        errors, _, _ = run(text, {"expect": [{"section": ".stack", "size": 1024}]})
        self.assertEqual(len(errors), 1)
        self.assertIn("declared 1024", errors[0])

    def test_entries_times_entry_bytes(self):
        text = MAP_HEADER + ".csa           0x0000000020000000      0x400\n"
        cfg = {"expect": [{"section": ".csa", "entries": 16, "entry_bytes": 64}]}
        errors, _, _ = run(text, cfg)
        self.assertEqual(errors, [])

    def test_missing_section_is_error_but_declared_zero_is_ok(self):
        text = MAP_HEADER + ".data          0x0000000020000000      0x10\n"
        errors, _, info = run(
            text,
            {"expect": [{"section": ".stack", "size": 64}, {"section": ".gone", "size": 0}]},
        )
        self.assertEqual(len(errors), 1)
        self.assertIn(".stack", errors[0])
        self.assertTrue(any(".gone" in m for m in info))

    def test_overlap_is_error(self):
        text = (
            MAP_HEADER
            + ".a            0x0000000020000000      0x200\n"
            + ".b            0x0000000020000100      0x200\n"
        )
        errors, _, _ = run(text, {})
        self.assertTrue(any(m.startswith("overlap") for m in errors))

    def test_adjacent_sections_do_not_overlap(self):
        text = (
            MAP_HEADER
            + ".a            0x0000000020000000      0x100\n"
            + ".b            0x0000000020000100      0x100\n"
        )
        errors, _, _ = run(text, {})
        self.assertEqual(errors, [])

    def test_past_region_end_is_error(self):
        text = MAP_HEADER + ".big          0x0000000020000f00      0x200\n"
        errors, _, _ = run(text, {})
        self.assertTrue(any("past end of RAM" in m for m in errors))

    def test_region_usage_warning(self):
        text = MAP_HEADER + ".fat          0x0000000020000000      0xf00\n"
        _, warnings, _ = run(text, {"check": {"region_warn_percent": 90}})
        self.assertEqual(len(warnings), 1)

    def test_sections_outside_regions_are_ignored(self):
        text = MAP_HEADER + ".debug_info   0x0000000000000000      0x500\n.debug_x      0x0000000000000100      0x500\n"
        errors, _, _ = run(text, {})
        self.assertEqual(errors, [])


class ExampleTests(unittest.TestCase):
    def test_baseline_map_passes(self):
        rc = cl.main(["-q", str(EX / "link-output/firmware.map"), str(EX / "config/layout.toml")])
        self.assertEqual(rc, 0)

    def test_stale_map_fails(self):
        rc = cl.main(["-q", str(EX / "link-output/firmware_stale.map"), str(EX / "config/layout.toml")])
        self.assertEqual(rc, 1)

    def test_bad_input_returns_2(self):
        rc = cl.main(["-q", str(EX / "does-not-exist.map"), str(EX / "config/layout.toml")])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
