# Glossary

## Method terms

| Term | Meaning |
|---|---|
| E1 to E4 | Evidence stages: source, build input, link, runtime |
| G0 to G7 | Gates a claim passes through, see [ARCHITECTURE.md](ARCHITECTURE.md) |
| Discriminator | The artifact that would prove or disprove a hypothesis |
| Stale value | A value that was correct for an earlier configuration and was not updated |
| Claim | A statement about the layout that needs evidence |

## Memory terms

**Stack.** Memory used for local variables, spills, and arguments passed on the stack. Sized per core.

**CSA (context save area).** On TriCore, hardware-managed storage for saved context on calls, interrupts, and traps. Entries are linked in a list through the FCX and LCX registers. Each entry is 16 words (64 bytes). Sizing depends on call depth and interrupt nesting.

**Interrupt nesting depth.** How many interrupt service routines can be active at once, bounded by the priority levels in use.

**Region.** A named memory range in a linker script, with origin, length, and attributes.

**Section.** A named block of code or data produced by the compiler and placed by the linker.

**Map file.** Linker output listing regions, section placements, sizes, and symbols. The authority on where things ended up.

**Overflow.** A section or region exceeds its size. At link time it is a linker error. At run time it is memory corruption or a trap.

**Orphan section.** An input section no rule in the linker script matches. The linker places it by default rules, which may not be where you want it.

**Core-local memory.** RAM attached to one core, with fast access. AURIX devices call the data and program variants DSPR and PSPR. Other cores see it through a different address window.

## Boot terms

**Core release.** Starting additional cores after reset, normally by the boot core.

**Startup code.** Code that runs before `main`: stack pointer and CSA list setup, clearing `.bss`, copying `.data`, other initialization.

**Trap.** A hardware exception for an invalid access, alignment fault, stack or context fault, and similar.

**Hang.** Execution stops without a trap. Causes include an infinite loop, a deadlock, disabled interrupts, or a core that was never released.

## Calibration terms

**A2L.** ASAM MCD-2 MC description file. Maps names to addresses and describes the measurement and calibration interface.

**XCP.** Measurement and calibration protocol that works with an A2L file.

**Page switch.** Changing between calibration pages, for example a working page and a reference page. If the description file and the firmware disagree on addresses, page switching can fail.

## Toolchain terms

**GNU ld.** The GNU linker, used by GCC-based toolchains including those for TriCore.

**Linker script.** The file that defines regions and the rules for placing sections.

**LMA and VMA.** Load address and run address. They differ for initialized data stored in flash and copied to RAM at startup.

## Hardware family

Infineon AURIX is a family of multi-core automotive microcontrollers based on TriCore. Derivatives differ in core count, memory sizes, and peripherals. Use the datasheet for the exact derivative. This repository gives no derivative-specific numbers.
