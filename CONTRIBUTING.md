# Contributing

Contributions are welcome: corrections, examples, toolchain notes, and tooling.

## Ground rules

These matter more than style.

1. Only contribute what you are allowed to publish. Do not submit material from your employer, a customer, or a vendor under NDA, even with names removed. If you are unsure, ask the owner first.
2. Do not copy vendor manuals, release notes, or configuration files. Link to public documents and describe in your own words.
3. Examples must be synthetic: invented project, invented modules, invented addresses. A real defect can inspire an example, but the example must not be reconstructable from your real project.
4. Facts must be checkable. Cite the public datasheet, manual, or specification for hardware and toolchain claims. If you are not sure, say so.

## What helps

- Corrections to technical content, with a source
- Notes on other linkers and toolchains, written by people who use them
- Synthetic examples for each mode
- A map file parser or checker, with tests, using synthetic input
- Clearer wording

## Workflow

```bash
git clone https://github.com/<your-fork>/embedded-memory-layout-guide.git
cd embedded-memory-layout-guide
git checkout -b docs/short-description
# edit, then
git commit -m "Short imperative summary"
git push origin docs/short-description
```

Open a pull request that says what changed, why, and what source supports it.

## Style

- Markdown, one H1 per file
- Plain language, no marketing wording
- Short sentences
- Tables for comparisons, code fences for anything a person might copy
- State assumptions and mark anything unverified

## Review

A maintainer checks scope, accuracy, source for technical claims, and that nothing in the change breaks the ground rules above.

## License

By contributing, you agree your contribution is licensed under the MIT License in [LICENSE](LICENSE).
