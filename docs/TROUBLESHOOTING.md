# Troubleshooting

Messages below are GNU ld messages. Wording varies slightly between binutils versions. Other linkers use other messages and are not covered here.

## Linker messages

| Message | Meaning | Likely causes | Checks |
|---|---|---|---|
| `region 'X' overflowed by N bytes` | Sections assigned to region X total more than its length | Region too small, too much static data, a section routed to the wrong region | Map file: sum the sections in X, compare to the region length. Read the last lines of the link output for the section that crossed the limit |
| `section '.x' will not fit in region 'X'` | One section is larger than the region | Same as above, or a region length typo | Section size in the map file against region length in the script |
| `undefined reference to 'sym'` | A symbol is used and never defined | Object or library not on the link line, section discarded by `--gc-sections`, missing `KEEP` | `nm` the objects, check the link command, check `KEEP` and `ENTRY` |
| `multiple definition of 'sym'` | Two objects define the same symbol | Header defines a variable, duplicated library, weak and strong mix-up | The two object names in the message |
| `relocation truncated to fit: <type> against 'sym'` | An address does not fit the instruction's reach | Code and callee too far apart for a short call, data outside the addressing window of a small-data base register | Addresses of caller and callee in the map file. Check compiler options for code model and small-data limits |
| `cannot move location counter backwards (from A to B)` | A location counter assignment moves below the current position | Region too small for what precedes it, wrong origin in a `. = ...` assignment | Print the counter with `PROVIDE` symbols or read the map file around the section |
| `section '.a' LMA [x,y] overlaps section '.b' LMA [z,w]` | Two sections load to overlapping flash addresses | Load region too small, overlapping `AT()` ranges | Compare load addresses in the map file |
| `warning: orphan section '.x' from 'f.o' being placed in section '.y'` | No rule matched `.x` | New section name from the compiler or a new attribute | Add an explicit rule, or check the section attribute in the source |
| `cannot open linker script file` or `cannot find -lname` | Input file not found | Path, name, or missing build step | The link command and the working directory |

## Linker script patterns

### First match wins

GNU ld assigns an input section to the first rule in script order that matches it. A broad pattern placed early takes sections meant for a later rule.

```
/* The broad rule below captures everything first */
.text : { *(.text*) } > FLASH
.fast_text : { *(.text.hot*) } > PSPR   /* never receives anything */
```

Put the specific rule before the general one:

```
.fast_text : { *(.text.hot*) } > PSPR
.text      : { *(.text*) } > FLASH
```

Confirm with the map file: the `.text.hot*` input sections should appear under `.fast_text`.

### Overlap without an error

Two output sections with explicit addresses can overlap in memory with no message if the script assigns them by hand. Compute each end address from the map file and compare to the next start.

### Section discarded

With `--gc-sections`, a section nothing references is dropped. Interrupt vector tables and tables only the hardware reads need `KEEP`.

## Boot failures

### Hang with no output

| Cause | How to see it | Fix direction |
|---|---|---|
| Stack pointer invalid or stack too small | SP outside the stack region in the debugger | Check startup code and stack region |
| CSA list not initialized or too small | Context-related trap, FCX at or near zero | Check CSA setup and entry count |
| Core never released | Other core stuck at its reset vector | Check boot core release sequence and start address |
| RAM init missing | Globals hold random values | Check `.bss` clear and `.data` copy |
| Interrupts or watchdog misconfigured | Resets at regular intervals | Check watchdog setup and startup timing |

### Trap at a specific address

1. Record the trap class and the program counter.
2. Find the symbol: search the map file near that address.
3. If the PC is in a data region, execution jumped through corrupted data.
4. Inspect stack and CSA state in the debugger.
5. Look for stack overflow, misaligned access, or an out-of-bounds write near the failing code.

### Works until an interrupt fires

Measure stack and CSA use under interrupt load. Compare to allocated sizes. Check nesting depth against the priority table.

## Calibration interface failures

If a calibration tool cannot read or switch pages, compare the addresses in the description file against the map file for every symbol the file references. If more than one description file exists, check all of them. A change that was applied to one file and not the others is a common cause.

## Checklist by stage

E1, source
- [ ] Config and linker script parse
- [ ] Expected values present
- [ ] No leftover values from a previous platform

E2, build input
- [ ] Generated headers contain the values
- [ ] Preprocessed linker script reads as intended

E3, link
- [ ] Link succeeds with no overflow
- [ ] Every section is in the expected region
- [ ] No overlaps or unexpected gaps

E4, runtime
- [ ] Stack pointers and CSA list in range
- [ ] Measured use within allocation
- [ ] No unexpected traps

## Useful commands

```
nm -S --size-sort build/firmware.elf        # symbol sizes
readelf -S build/firmware.elf               # section headers
objdump -h build/firmware.elf               # sections with LMA and VMA
```

Preprocess a linker script that uses the C preprocessor:

```
cpp -P -x c -DSOME_FLAG=1 linker/sections.ld > build/sections.pp.ld
```

## When asking for help

Include the exact message, the relevant map file excerpt, the relevant linker script excerpt, and the configuration value. Remove anything you are not allowed to share before posting.
