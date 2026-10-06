# Architecture of the Method

This document defines the data model and rules behind the five modes. Read it if you want to apply the method rigorously, write tooling around it, or contribute.

## Principles

1. Evidence first. A claim is as strong as its artifact.
2. Project isolation. Values from another project are hints, never inputs.
3. Defensibility. For every value you can show where it was declared, where it was built, where it was placed, and, where it matters, how it behaved.

A weak statement: "Stack is 4 KB."

A defensible one: "Core 0 stack is 4 KB. Static analysis gives 2.6 KB worst case, the OS needs 0.5 KB, margin is 25 percent. Declared in the layout config, present in the generated header, placed by the linker at the address in the map file, and 2.1 KB was in use at the end of boot."

## Evidence stages

| Stage | Artifact | Typical check |
|---|---|---|
| E1 | Source: linker script, layout configuration | grep for the value |
| E2 | Generated or preprocessed build input | grep generated headers, preprocess the linker script and read it |
| E3 | Linker map file | Section address, size, region, overlaps |
| E4 | Runtime | Debugger memory read, boot log, trap capture |

## Claim status

| Status | Meaning |
|---|---|
| CONFIRMED | Backed at the stage required for this kind of claim |
| DERIVED | Computed from confirmed inputs, not yet placed or observed |
| HYPOTHESIS | Plausible, no evidence yet |
| CONTRADICTED | Two sources disagree |
| UNKNOWN | Not yet discovered |

## Gates

| Gate | Question | Evidence |
|---|---|---|
| G0 Context | Do we know the derivative, boot flow, OS, toolchain? | Filled project facts with sources |
| G1 Ownership | Which files may we edit, which are generated? | File classification |
| G2 Constraints | What do hardware and OS require? | Datasheet and manual references |
| G3 Source | Is the value declared? | E1 |
| G4 Propagation | Did it reach the build? | E2 |
| G5 Placement | Did the linker place it correctly? | E3 |
| G6 Runtime | Does the target behave as claimed? | E4 |
| G7 Knowledge | Is the decision written down? | Decision record |

A report states which gates passed, which failed, and which are unknown. Unknown is not pass.

## Project facts

A project fact sheet, as a plain file:

```yaml
project: example-ecu
mcu:
  derivative: <from datasheet>
  cores: <n>
  ram_global: <size>
  ram_per_core: <size>
boot:
  loader: <name and version>
  core_start: <which cores start in which phase>
os:
  name: <name and version>
  min_stack_bytes: <from OS docs>
toolchain:
  linker: <name and version>
application:
  max_interrupt_nesting: <measured or from priority table>
  worst_case_call_depth_bytes: <static analysis>
policy:
  margin_percent: <stated>
```

Each field carries a source or the word UNKNOWN.

## Claim record

```yaml
claim: Core0 stack is 4096 bytes
status: CONFIRMED
stage: E3
source:   {file: config/layout.yaml, line: 12}
build:    {file: build/generated/layout.h, line: 8}
link:     {file: build/firmware.map, excerpt: ".stack_core0 0x70001000 0x1000"}
runtime:  null
assumptions:
  - Margin of 25 percent is adequate for the measured load case
conflicts: null
```

## Change authority

Decide per project who may approve each kind of change. A common split:

| Level | Scope | Example |
|---|---|---|
| A | Affects other projects or shared framework behavior | Changing a context save area convention |
| B | Affects this project's layout or boot sequence | New derivative, new stack sizes |
| C | Local, no cross-project effect | Margin policy for one module |

## Minimal change principle

When several things might be wrong, fix and test them one at a time. A single change per test tells you which change fixed which symptom.

## Pattern entries

Reusable findings are kept as short entries:

```yaml
pattern: Linker script wildcard order
category: toolchain behavior
statement: GNU ld assigns an input section to the first matching pattern in script order.
effect: A broad pattern placed early captures sections meant for a later, more specific rule.
detection: Map file shows a section in an unexpected output section or region.
fix: Put specific patterns before general ones, or use EXCLUDE_FILE.
scope: GNU ld
```

## Using the method in tooling

A tool can implement the same steps:

1. Parse the map file into sections with address, size, and region.
2. Parse configuration for declared values.
3. Compare declared and placed values, flag mismatches, overlaps, and regions above a usage threshold.
4. Emit a gate report.

A CI job that fails a build when declared and placed values differ catches most stale-value defects before they reach a target.
