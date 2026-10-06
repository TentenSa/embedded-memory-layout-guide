# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] Unreleased

### Included

- Method: evidence stages E1 to E4, gates G0 to G7, five modes
- Documentation: quick start, user guide, architecture, glossary, troubleshooting
- One synthetic example with a linker script, a layout configuration, and a map excerpt

### Not included yet

- Any tool or script
- Validation on hardware. All examples are synthetic and unverified on a target.
- Toolchain coverage beyond GNU ld

### Known limitations

- Hardware numbers are illustrative. Use the datasheet for your derivative.
- Message wording follows GNU ld and varies between binutils versions.

## Roadmap

### 0.2.0
- Map file parser that reports declared against placed values, overlaps, and region usage
- Second example: migration between two synthetic memory maps

### 0.3.0
- CI example that fails a build on declared and placed mismatch
- Notes for other linkers, contributed by people who use them
