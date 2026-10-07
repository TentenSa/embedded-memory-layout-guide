# User Guide

This guide covers the five modes. All numbers are illustrative. Take real constraints from your derivative's datasheet and user manual, your OS documentation, and your own measurements.

## Contents

1. [Before you start](#before-you-start)
2. [Mode 1: Design](#mode-1-design)
3. [Mode 2: Investigate](#mode-2-investigate)
4. [Mode 3: Migrate](#mode-3-migrate)
5. [Mode 4: Decode a linker error](#mode-4-decode-a-linker-error)
6. [Mode 5: Audit](#mode-5-audit)
7. [Common pitfalls](#common-pitfalls)

## Before you start

Collect, and keep in a text file next to the project:

- Derivative, core count, role of each core
- Flash and RAM map: global RAM, per-core local RAM, any reserved areas
- Bootloader, OS, framework and their versions
- Toolchain and linker flavor
- Paths to the linker script, generated linker inputs, configuration files, the latest map file, and the build log

Any field you cannot fill is UNKNOWN. Do not guess it. Mark it and find the source.

## Mode 1: Design

Goal: values you can defend, derived from this project's constraints.

### 1. Constraints

| Source | Typical content |
|---|---|
| Datasheet and user manual | Memory map, core-local RAM sizes, alignment rules, context save area format |
| OS documentation | Minimum stack per core or task, kernel RAM, interrupt model |
| Bootloader documentation | Reserved regions, which core starts when |
| Your code | Deepest call chain, largest interrupt handler, priority levels in use |

### 2. Derive

Stack per core:

```
stack = worst_case_call_depth_bytes      (static stack analysis, not a guess)
      + os_overhead_bytes                (from OS documentation)
      + margin                           (stated policy, for example 25 percent)
```

Round up to the alignment your architecture requires. TriCore stacks are 8-byte aligned.

Context save areas (TriCore): each call and each interrupt or trap entry uses context save area entries. On AURIX each entry is 16 words (64 bytes) and the area is managed through the FCX and LCX registers. A conservative count is:

```
csa_entries = max_call_depth
            + sum over nested interrupt levels of (entries per interrupt entry)
            + trap_reserve
            + margin
```

Check the exact per-call and per-interrupt consumption in the architecture manual for your core, and confirm the maximum list size your derivative allows.

### 3. Record the derivation

Write the arithmetic down next to the value, with the source of each input:

```
Core0 stack = 3.1 KB (static analysis, tool X, build 1234)
            + 0.5 KB (OS doc, section name)
            + 25 percent
            = 4.5 KB -> 5 KB (8-byte aligned, rounded to 1 KB)
```

### 4. Configure, build, link

Set the value in your configuration (E1). Rebuild. Confirm it appears in generated input (E2). Confirm placement and size in the map file (E3).

### 5. Runtime check

Stop at `main` and again under worst-case interrupt load. Record stack used and CSA entries used. Compare to allocated. This is E4.

### 6. Decision record

```
Decision: Core0 stack 5 KB, CSA 64 entries
Reason:   derivation above
Evidence: config line, generated header line, map line, debugger capture
Status:   E3 proven, E4 captured under load case A only
Revisit:  when OS version or interrupt priorities change
```

Mode 1 is complete when gates G0 to G5 pass and G6 and G7 are either passed or explicitly open.

## Mode 2: Investigate

Goal: a root cause backed by E3 or E4, not the first plausible story.

### 1. Capture the symptom exactly

Tool, operation, error text or code, first build where it appeared, what changed since the last good build, whether it is consistent, and its scope.

### 2. List at least four hypotheses

Do not stop at the first one.

### 3. Name a discriminator for each

The discriminator is the artifact that would prove or disprove it.

### 4. Collect, then eliminate

Illustrative case: a calibration tool cannot switch pages after a bootloader update.

| Hypothesis | Discriminator | Check |
|---|---|---|
| Descriptor file has an old address for a shared RAM structure | Map file vs descriptor file | Compare the symbol address in both |
| A second descriptor file was not updated | All descriptor copies | `grep -rn <old address> config/` |
| Calibration segment now overlaps that structure | Map file section table | Compare start and end addresses |
| Protocol parameters differ between tool and firmware | Descriptor vs firmware constants | Compare field by field |
| Checksum algorithm changed | Bootloader release notes | Read the notes |

Evidence from a typical outcome: the map file places the structure at one address, one descriptor file has the new address and another still has the old one. Root cause: two descriptor files, one updated. Fix: update the second file, then rebuild and retest.

A worked synthetic case, where the checker passes and the cause is a derivation with no margin, is in [examples/boot-failure-csa-depletion](../examples/boot-failure-csa-depletion).

### 5. Apply the smallest fix, then retest

Change one thing. If the symptom remains, change the next. Do not bundle fixes: you will not know which one worked.

### 6. Write it down

Symptom, root cause, evidence at each stage, fix, and what you could not prove.

## Mode 3: Migrate

Goal: find every stale value before it finds you.

1. Extract the old and new memory maps side by side: region origins and lengths, core-local ranges, reserved areas.
2. Diff configuration files per module. Do not assume modules changed together.
3. List every value that encodes an address or a size: stack, CSA, region lengths, calibration segment definitions, descriptor files, bootloader handoff addresses.
4. Update them all, build, and read the map file for overlaps and gaps.
5. Test change categories separately: regions first, then boot and core start, then stack and CSA, then calibration interfaces.
6. Record what changed and why.

A worked synthetic case, with the checker run on a half-migrated project, is in [examples/migration-device-upgrade](../examples/migration-device-upgrade).

Search for leftovers by old derivative name and old addresses:

```
grep -rniE "oldderivative|0xOLDADDR" config/ linker/ tools/
```

## Mode 4: Decode a linker error

Use [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Confirm the cause in the map file before changing anything.

## Mode 5: Audit

Check each gate and record pass, fail, or unknown:

| Gate | Check |
|---|---|
| G0 | Context fields filled from sources |
| G1 | You know which files are hand-edited and which are generated |
| G2 | Hardware and OS constraints are documented with sources |
| G3 | Each value is present in configuration |
| G4 | Each value reached generated build input |
| G5 | Map file confirms address, size, no overlap |
| G6 | Runtime capture exists for critical values |
| G7 | Decisions are written down |

Report: gates passed, gates unknown, and the evidence missing for each unknown.

## Common pitfalls

- Sizing from a previous project instead of deriving.
- Editing a generated file and losing the change at the next build.
- Updating one of several files that carry the same address.
- Trusting a comment that says a value was validated.
- Reading E1 as proof of E3. The linker is the authority on placement.
- Sizing the stack and forgetting the context save area, or the reverse.
- Allowing a wildcard in the linker script to catch sections you did not intend. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
