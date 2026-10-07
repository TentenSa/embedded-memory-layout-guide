# Example: boot trap from context list depletion (synthetic, Mode 2)

An invented project traps on core 0 after a new interrupt handler is added. Everything here is made up: the device, addresses, function names, and the capture. The link maps are real GNU ld output from a dummy object.

The lesson: declared and placed values agreed at every stage up to the map file. The defect was in the derivation, and only runtime evidence (E4) showed it.

## Files

```
src/dummy.c               placeholder code for the linker
before/                   the failing build: 16 CSA entries on core 0
  sections.ld, memory.ld  same scripts as examples/dualcore-baseline
  layout.toml             declarations
  firmware.map            trimmed excerpt of a real GNU ld map
after/                    the fixed build: 32 CSA entries
trap_capture.txt          synthetic debugger capture of the failure
```

## 1. Symptom

- After adding a new SPI interrupt handler, the device traps shortly after boot on core 0
- The trap class is context management (free context list depletion), taken as the new handler's interrupt was being entered
- Consistent, only when interrupt load is present, not on an idle bench
- The last good build had one fewer interrupt level and a shallower call chain

Details are in `trap_capture.txt`. Only the data memory addresses in the capture (context list area, stack region) are tied to the maps, and a test checks that. The code address and function names are invented and do not exist in the dummy object. Check the exact class and identification number for your core in the architecture manual before relying on a name.

## 2. Hypotheses

| # | Hypothesis | Discriminator |
|---|---|---|
| H1 | Stack overflow on core 0 | SP at trap against the stack region from the map |
| H2 | Context save list ran out | FCX and LCX at trap, entries in use against list size |
| H3 | Declared and placed values disagree (stale value) | `check_layout.py` on the failing build |
| H4 | Free list was corrupted by a stray write | Walk the chain: do all links stay inside the list area |
| H5 | Another core is involved (not released, cross-core fault) | Which core trapped, state of the others |

## 3. Evidence

| # | Evidence | Result |
|---|---|---|
| H1 | SP `0x30000d80`, region `0x30000400` to `0x300013ff`, 1664 of 4096 bytes in use | Ruled out. Stack is 40 percent used and SP is inside the region |
| H3 | `python ../../tools/check_layout.py before/firmware.map before/layout.toml` | Ruled out. 0 errors: 16 entries declared, 16 placed |
| H4 | Every link on the used chain points inside `0x30000000` to `0x300003ff` | Ruled out. Chain is intact |
| H5 | Trap is on core 0, the core that owns the list | Ruled out |
| H2 | FCX equals LCX, 14 of 16 entries in use, 2 held back | Confirmed. The list is full |

Stage reached: E4. Nothing at E1 to E3 was wrong, which is why the checker passed.

The used chain explains the count: 8 entries from a call chain (one per call) plus 6 from three nested interrupts (two per interrupt entry, upper and lower context). The fourth interrupt, the new handler, needed two more and the list had only the held-back entries left.

## 4. Root cause

The derivation behind the 16 entries had no margin:

```
before:  call depth 8  +  3 interrupt levels x 2  +  trap reserve 2  =  16   (margin 0)
```

Two changes consumed it. The new handler added a fourth interrupt priority level, and a driver call chain got deeper. The declaration, the build, and the link all faithfully reproduced a number that was too small.

Confirm per-call and per-interrupt consumption against the architecture manual for your core. The counts above follow the usual TriCore model but are synthetic.

## 5. Fix, smallest change

Re-derive, then change one value.

```
after:   worst-case call depth 12
       + 4 interrupt levels x 2          = 8
       + trap reserve                    = 2
       = 22, plus 25 percent margin      = 27.5  ->  32 entries (2048 bytes)
```

Change only `CSA_CORE0_COUNT` (and its declaration). Do not change the stack in the same step: it is not the cause, and changing it would make it impossible to know which change fixed the trap.

```
python ../../tools/check_layout.py after/firmware.map after/layout.toml
python ../../tools/check_layout.py after/firmware.map before/layout.toml   # fails: stale declaration
```

The second command shows the other half of the problem: if only the build moves, the declaration is stale.

## 6. Verify

1. E3: the checker passes on `after/`, and `.csa_core0` is `0x800` bytes in `after/firmware.map`
2. E4: rerun the worst-case interrupt load and record the peak number of entries in use. The fix is proven when the peak is comfortably under the usable count, for example 21 of 30 usable, and not before
3. Record the derivation, the old and new values, and the measured peak next to the value, so the next change starts from evidence

## 7. What to take from it

- A passing checker means declarations and placement agree. It does not mean the value is right
- Derive with a stated margin. A value with zero margin fails on the next change
- Keep the call chain and interrupt level count as inputs to the CSA count, and recheck both when either changes
- Measure the peak at run time. Static derivation gives the sizing, E4 gives the proof

## Exercise

1. Which of H1 to H5 would the checker have caught? (H3 only.)
2. Change the capture so SP is at `0x30000420`. What does that change about H1? (Stack near the limit, and it becomes the lead hypothesis.)
3. Write the derivation for a project with 6 call frames and 2 interrupt levels, margin 25 percent. What is the entry count and the byte size? (6 + 2 x 2 + 2 reserve = 12, times 1.25 = 15, rounds up to 16 entries, 1024 bytes.)
4. List two ways the count could be wrong that a debugger capture at idle would never show.
