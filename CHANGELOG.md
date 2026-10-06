# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] Unreleased

### Added

- `tools/check_layout.py`: compares declared sizes in a TOML file against a GNU ld map. Reports size mismatches, missing sections, overlaps, sections past region end, and region usage over a threshold
- Unit tests, including a test that the stale example map must fail, and an offline check of relative markdown links
- GitHub Actions workflow that runs the tests and the checker on the example

- Optional `addr` in an expectation, to catch fixed-address structures that moved
- Second example, `migration-device-upgrade` (Mode 3), with real GNU ld maps for an old and a new synthetic device

### Changed

- Example configuration is now `layout.toml` so the checker needs no third-party package

### Known limitations

- Run addresses only. Load addresses (flash images of initialized data) are not counted
- Parses top-level output sections. It does not attribute sizes to input files
- Tested against GNU ld 2.42 output and synthetic text, not against every binutils version or any TriCore toolchain map

## [0.1.0]

### Included

- Method: evidence stages E1 to E4, gates G0 to G7, five modes
- Documentation: quick start, user guide, architecture, glossary, troubleshooting
- One synthetic example with a linker script, a layout configuration, and a map excerpt

### Not included yet

- Any tool or script (added in 0.2.0)
- Validation on hardware. All examples are synthetic and unverified on a target.
- Toolchain coverage beyond GNU ld

### Known limitations

- Hardware numbers are illustrative. Use the datasheet for your derivative.
- Message wording follows GNU ld and varies between binutils versions.

## Roadmap

### 0.3.0
- Load address (LMA) checks for flash images
- Notes for other linkers, contributed by people who use them
