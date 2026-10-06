#!/usr/bin/env python3
"""Check a GNU ld map file against declared layout expectations.

Reads the output-section table from a map file and a TOML file that lists
what you declared. Reports:

  * declared size, entry count, or address that differs from the placed section
  * declared sections that are missing from the map
  * output sections whose address ranges overlap
  * sections that run past the end of their memory region
  * regions filled beyond a warning threshold

Standard library only. Python 3.11 or newer (tomllib).

Exit status: 0 if no errors, 1 if any error, 2 for bad input.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    name: str
    origin: int
    length: int

    @property
    def end(self) -> int:
        return self.origin + self.length

    def contains(self, addr: int) -> bool:
        return self.origin <= addr < self.end


@dataclass(frozen=True)
class Section:
    name: str
    addr: int
    size: int

    @property
    def end(self) -> int:
        return self.addr + self.size


_HEX = r"0x[0-9a-fA-F]+"
_REGION_RE = re.compile(rf"^(\S+)\s+({_HEX})\s+({_HEX})(?:\s+\S+)?\s*$")
_SECTION_RE = re.compile(rf"^(\.\S+)\s+({_HEX})\s+({_HEX})(?:\s|$)")
_SECTION_NAME_ONLY_RE = re.compile(r"^(\.\S+)\s*$")
_SECTION_CONT_RE = re.compile(rf"^\s+({_HEX})\s+({_HEX})(?:\s|$)")


def parse_map(text: str) -> tuple[list[Region], list[Section]]:
    """Return memory regions and top-level output sections from a ld map."""
    regions: list[Region] = []
    sections: list[Section] = []
    lines = text.splitlines()

    in_memory_config = False
    pending_name: str | None = None

    for line in lines:
        if line.strip() == "Memory Configuration":
            in_memory_config = True
            continue
        if line.startswith("Linker script and memory map"):
            in_memory_config = False
            continue

        if in_memory_config:
            m = _REGION_RE.match(line)
            if m and m.group(1) not in ("Name", "*default*"):
                regions.append(
                    Region(m.group(1), int(m.group(2), 16), int(m.group(3), 16))
                )
            continue

        if pending_name is not None:
            m = _SECTION_CONT_RE.match(line)
            if m:
                sections.append(
                    Section(pending_name, int(m.group(1), 16), int(m.group(2), 16))
                )
            pending_name = None
            if m:
                continue

        m = _SECTION_RE.match(line)
        if m:
            sections.append(
                Section(m.group(1), int(m.group(2), 16), int(m.group(3), 16))
            )
            continue
        m = _SECTION_NAME_ONLY_RE.match(line)
        if m:
            pending_name = m.group(1)

    return regions, sections


def region_of(regions: list[Region], addr: int) -> Region | None:
    for r in regions:
        if r.contains(addr):
            return r
    return None


def expected_size(entry: dict) -> int | None:
    if "size" in entry:
        return int(entry["size"])
    if "entries" in entry:
        return int(entry["entries"]) * int(entry.get("entry_bytes", 64))
    return None


def check(
    regions: list[Region],
    sections: list[Section],
    config: dict,
) -> tuple[list[str], list[str], list[str]]:
    """Return (errors, warnings, info) message lists."""
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    by_name = {s.name: s for s in sections}
    warn_pct = float(config.get("check", {}).get("region_warn_percent", 90))

    # 1. Declared against placed
    for entry in config.get("expect", []):
        name = entry.get("section")
        want = expected_size(entry)
        if not name or want is None:
            errors.append(f"config entry needs 'section' and 'size' or 'entries': {entry}")
            continue
        sec = by_name.get(name)
        if sec is None:
            if want == 0:
                info.append(f"{name}: declared 0, absent from map (ok)")
            else:
                errors.append(f"{name}: declared {want} bytes, section not found in map")
            continue
        ok = True
        if sec.size != want:
            ok = False
            errors.append(
                f"{name}: declared {want} (0x{want:x}) bytes, "
                f"map places {sec.size} (0x{sec.size:x}) bytes"
            )
        if "addr" in entry and sec.addr != int(entry["addr"]):
            ok = False
            want_addr = int(entry["addr"])
            errors.append(
                f"{name}: declared address 0x{want_addr:x}, "
                f"map places it at 0x{sec.addr:x}"
            )
        if ok:
            info.append(f"{name}: {sec.size} bytes at 0x{sec.addr:x} matches declaration")

    # 2. Only sections that sit inside a known region take part in layout checks
    placed = [s for s in sections if s.size > 0 and region_of(regions, s.addr)]

    # 3. Overlaps (address ranges)
    ordered = sorted(placed, key=lambda s: (s.addr, s.end))
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            if b.addr >= a.end:
                break
            errors.append(
                f"overlap: {a.name} [0x{a.addr:x}, 0x{a.end:x}) and "
                f"{b.name} [0x{b.addr:x}, 0x{b.end:x})"
            )

    # 4. Past region end
    for s in placed:
        r = region_of(regions, s.addr)
        assert r is not None
        if s.end > r.end:
            errors.append(
                f"{s.name}: ends at 0x{s.end:x}, past end of {r.name} (0x{r.end:x})"
            )

    # 5. Region usage
    for r in regions:
        used = sum(s.size for s in placed if region_of(regions, s.addr) is r)
        pct = 100.0 * used / r.length if r.length else 0.0
        line = f"{r.name}: {used} of {r.length} bytes used ({pct:.1f} percent)"
        if pct >= warn_pct:
            warnings.append(line + f", at or above {warn_pct:g} percent")
        else:
            info.append(line)

    return errors, warnings, info


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("map_file", help="GNU ld map file")
    p.add_argument("config", help="TOML file with [[expect]] entries")
    p.add_argument("-q", "--quiet", action="store_true", help="only print errors and warnings")
    args = p.parse_args(argv)

    try:
        with open(args.map_file, encoding="utf-8", errors="replace") as f:
            regions, sections = parse_map(f.read())
        with open(args.config, "rb") as f:
            config = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not regions or not sections:
        print("error: no memory regions or output sections found in the map file", file=sys.stderr)
        return 2

    errors, warnings, info = check(regions, sections, config)

    if not args.quiet:
        for m in info:
            print(f"ok     {m}")
    for m in warnings:
        print(f"WARN   {m}")
    for m in errors:
        print(f"ERROR  {m}")

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
