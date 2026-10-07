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

    def test_declared_address_mismatch_is_error(self):
        text = MAP_HEADER + ".mailbox       0x0000000020000100       0x40\n"
        cfg = {"expect": [{"section": ".mailbox", "size": 64, "addr": 0x20000000}]}
        errors, _, _ = run(text, cfg)
        self.assertEqual(len(errors), 1)
        self.assertIn("declared address 0x20000000", errors[0])

    def test_declared_address_match_passes(self):
        text = MAP_HEADER + ".mailbox       0x0000000020000100       0x40\n"
        cfg = {"expect": [{"section": ".mailbox", "size": 64, "addr": 0x20000100}]}
        errors, _, _ = run(text, cfg)
        self.assertEqual(errors, [])

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


MIG = ROOT / "examples" / "migration-device-upgrade"


class MigrationExampleTests(unittest.TestCase):
    def test_old_map_with_old_config_passes(self):
        rc = cl.main(["-q", str(MIG / "old/firmware.map"), str(MIG / "old/layout.toml")])
        self.assertEqual(rc, 0)

    def test_new_map_with_old_config_fails_on_address_and_stacks(self):
        regions, sections = cl.parse_map((MIG / "new/firmware.map").read_text())
        import tomllib
        cfg = tomllib.loads((MIG / "old/layout.toml").read_text())
        errors, _, _ = cl.check(regions, sections, cfg)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("declared address 0x20000000" in e for e in errors))

    def test_new_map_with_new_config_passes(self):
        rc = cl.main(["-q", str(MIG / "new/firmware.map"), str(MIG / "new/layout.toml")])
        self.assertEqual(rc, 0)


BF = ROOT / "examples" / "boot-failure-csa-depletion"


def _hex_range(text, label):
    import re
    m = re.search(label + r"\s*:\s*(0x[0-9a-f]+)\s*-\s*(0x[0-9a-f]+)", text)
    assert m, f"{label} not found in capture"
    return int(m.group(1), 16), int(m.group(2), 16)


class BootFailureExampleTests(unittest.TestCase):
    def test_before_build_passes_the_checker(self):
        rc = cl.main(["-q", str(BF / "before/firmware.map"), str(BF / "before/layout.toml")])
        self.assertEqual(rc, 0)

    def test_after_build_passes_the_checker(self):
        rc = cl.main(["-q", str(BF / "after/firmware.map"), str(BF / "after/layout.toml")])
        self.assertEqual(rc, 0)

    def test_after_build_with_stale_declaration_fails(self):
        rc = cl.main(["-q", str(BF / "after/firmware.map"), str(BF / "before/layout.toml")])
        self.assertEqual(rc, 1)

    def test_capture_matches_the_before_map(self):
        import re
        capture = (BF / "trap_capture.txt").read_text()
        _, sections = cl.parse_map((BF / "before/firmware.map").read_text())
        by = {s.name: s for s in sections}

        csa_lo, csa_hi = _hex_range(capture, r"list area")
        self.assertEqual(csa_lo, by[".csa_core0"].addr)
        self.assertEqual(csa_hi + 1, by[".csa_core0"].end)

        stk_lo, stk_hi = _hex_range(capture, r"region")
        self.assertEqual(stk_lo, by[".stack_core0"].addr)
        self.assertEqual(stk_hi + 1, by[".stack_core0"].end)

        sp = int(re.search(r"SP at trap\s*:\s*(0x[0-9a-f]+)", capture).group(1), 16)
        self.assertTrue(stk_lo <= sp <= stk_hi + 1, "SP must be inside the stack region (H1 ruled out)")

        entries = (csa_hi + 1 - csa_lo) // 64
        used = int(re.search(r"entries in use\s*:\s*(\d+)", capture).group(1))
        free = int(re.search(r"entries free\s*:\s*(\d+)", capture).group(1))
        self.assertEqual(used + free, entries)

    def test_after_build_has_the_documented_entry_count(self):
        _, sections = cl.parse_map((BF / "after/firmware.map").read_text())
        csa = {s.name: s for s in sections}[".csa_core0"]
        self.assertEqual(csa.size // 64, 32)


if __name__ == "__main__":
    unittest.main()
