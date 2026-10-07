# Examples

All examples are synthetic: invented devices, invented addresses, invented numbers. Please keep it that way. See [CONTRIBUTING.md](../CONTRIBUTING.md).

| Example | Mode | What it shows |
|---|---|---|
| [dualcore-baseline](dualcore-baseline) | 1 Design, 2 Investigate | Declared values, linker script, real GNU ld map excerpt, and a stale-value exercise |
| [boot-failure-csa-depletion](boot-failure-csa-depletion) | 2 Investigate | A boot trap where declarations, build and link all agree, hypotheses ruled out one by one, and why only runtime evidence found it |
| [migration-device-upgrade](migration-device-upgrade) | 3 Migrate | Old and new device, a moved fixed-address structure, changed stack sizes, and what the checker can and cannot see |

Wanted:

- A linker script for a toolchain other than GNU ld, written by someone who uses it
- A dual-bank firmware update layout
