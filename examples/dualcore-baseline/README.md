# Example: dual-core baseline (synthetic)

An invented 3-core device where only cores 0 and 1 are used. Everything here is made up: the device, the addresses, the sizes, the numbers in the derivation. The point is to show the evidence chain from source to map file.

## Files

```
config/layout.yaml          E1  declared stack and CSA sizes
linker/memory.ld                regions
linker/sections.ld          E2  consumes sizes through --defsym, places sections
link-output/firmware.map    E3  trimmed map excerpt from a real link
link-output/firmware_stale.map  same build with one value out of sync
```

## How the map was produced

The linker script was linked with GNU ld 2.42 on an x86-64 host against a small dummy object, using:

```
ld -nostdlib -static -e _start -T linker/sections.ld \
   --defsym=STACK_CORE0_SIZE=4096 --defsym=STACK_CORE1_SIZE=4096 \
   --defsym=CSA_CORE0_COUNT=64   --defsym=CSA_CORE1_COUNT=64 \
   -Map=firmware.map -o firmware.elf dummy.o
```

This checks script syntax and placement logic. It does not run on a TriCore target, so there is no E4 evidence here.

If you drop a `--defsym`, the link stops with `undefined symbol 'CSA_CORE0_COUNT' referenced in expression`. That is intended: no silent defaults.

## Derivation (illustrative)

| Item | Value | Source in a real project |
|---|---|---|
| Static worst-case call depth, core 0 | 2.6 KB | Static stack analysis tool output |
| OS overhead | 0.5 KB | OS documentation |
| Margin | 25 percent | Project policy |
| Total | 3.9 KB, rounded to 4 KB | Arithmetic, 8-byte aligned |
| CSA entries | 64 | Derived from call depth and interrupt nesting, see USER_GUIDE |
| CSA bytes | 64 x 64 = 4096 | 16 words per entry |

## Walk the evidence chain

Claim: core 0 stack is 4096 bytes.

| Stage | Where | What you see |
|---|---|---|
| E1 | `config/layout.yaml`, `cores.core0.stack_bytes` | 4096 |
| E2 | the `--defsym` on the link command | `STACK_CORE0_SIZE=4096` |
| E3 | `link-output/firmware.map` | `.stack_core0 0x30001000 0x1000` |
| E4 | not captured | Would be: read SP at `main` and under worst-case load |

Region check for core 0 local memory (length 0x4000): CSA 0x1000 + stack 0x1000 + data 0x4b0 = 0x24b0 used, 0x1b50 free.

## Exercise: find the stale value

Compare the two map files:

```
diff link-output/firmware.map link-output/firmware_stale.map
```

1. Which section changed size, and by how much?
2. Which declared value in `config/layout.yaml` does that contradict?
3. Which stage disagrees with which? (E1 against E3.)
4. Why did the linker not complain?
5. What check would catch this in CI before anyone reads a map file?

Answers: core 1's stack is 0x800 in the stale map while the config says 4096. The linker has no way to know the config exists, so it placed what it was given. A post-link check that compares declared sizes to placed section sizes would fail the build.
