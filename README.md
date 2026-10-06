# Embedded Memory Layout Guide

An evidence-based method for designing, checking, and debugging memory layouts on multi-core embedded targets, with a focus on AUTOSAR Classic projects on Infineon AURIX (TriCore) devices.

Status: documentation and one synthetic example. No tool yet. See [CHANGELOG.md](CHANGELOG.md) and the roadmap there.

## The problem

Memory layout values (stack sizes, context save area counts, region boundaries, core-local placement) are usually copied from the previous project and rarely justified. When something breaks, a boot trap, a linker overflow, or a calibration tool that reads the wrong address, the cause is often a value that was correct in one file and stale in another.

## The method

Every claim about a layout ("core 0 stack is 4 KB") is only as strong as the artifact that backs it:

| Stage | Artifact | Meaning |
|---|---|---|
| E1 | Configuration or linker script source | The value is declared |
| E2 | Generated or preprocessed build input | The value reached the build |
| E3 | Linker map file | The linker placed it at this address with this size |
| E4 | Debugger capture, boot log, trap capture | The target behaves as claimed |

A design decision is treated as proven at E3. A defect root cause needs E3 or E4. Anything at E1 only is a hypothesis.

Claims also pass through gates G0 to G7 (context, ownership, constraints, source, propagation, placement, runtime, documentation). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Five working modes

| Mode | Use it when | Result |
|---|---|---|
| 1 Design | Starting a new layout | Derived values with stated assumptions |
| 2 Investigate | Boot trap, hang, overflow, wrong runtime address | Ranked hypotheses, discriminating evidence, root cause |
| 3 Migrate | New derivative, toolchain, or framework version | List of stale values and a test order |
| 4 Decode | Linker error message | Likely causes and checks |
| 5 Audit | Pre-release review | Gate report with gaps |

## Where to start

1. [docs/QUICK_START.md](docs/QUICK_START.md), five minutes
2. [docs/USER_GUIDE.md](docs/USER_GUIDE.md), each mode in detail
3. [examples/dualcore-baseline](examples/dualcore-baseline), a synthetic project with a linker script and map excerpt
4. [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), common GNU ld messages and boot failure patterns
5. [docs/GLOSSARY.md](docs/GLOSSARY.md)

## Scope

| Target | Toolchain | Coverage |
|---|---|---|
| Infineon AURIX TC2xx, TC3xx | GCC based (GNU ld) | Primary |
| Infineon AURIX | Other TriCore toolchains | Concepts only |
| Other multi-core MCUs | GNU ld | Concepts apply, examples are AURIX style |

All hardware numbers in this repository are illustrative. Take real values from the datasheet and user manual of your exact derivative.

## What this repository does not contain

No vendor documentation, no vendor configuration files, and no data from any employer or customer project. Examples are synthetic. Please keep contributions the same way. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
