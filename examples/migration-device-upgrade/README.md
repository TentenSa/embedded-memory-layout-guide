# Example: device upgrade (synthetic, Mode 3)

An invented old device (2 of 3 cores used) is replaced by an invented new device (3 cores used, more memory). Everything here is made up. The example shows how to find stale values after a migration, and what the checker can and cannot see.

## Files

```
src/dummy.c           placeholder code so the linker has input sections
old/memory.ld         regions, old device
old/sections.ld       placement rules, old device
old/layout.toml       declarations for the old device
old/firmware.map      trimmed excerpt of a real GNU ld map
new/                  the same four files for the new device
```

## What changed between the devices

| Item | Old | New | Why it matters |
|---|---|---|---|
| RAM origin | 0x20000000 | 0x20008000 | First 32 KB reserved by the new boot flow. Anything at a fixed RAM address moves |
| Shared mailbox address | 0x20000000 | 0x20008000 | An external tool reads this structure at a fixed address |
| Core 0 and 1 stack | 4096 | 8192 | New OS needs more |
| Core 2 | unused | stack 4096, CSA 32 entries | New core in use |
| Core-local RAM | 16 KB | 32 KB each | More room, different budget |

## Reproduce the maps

```
gcc -c -ffreestanding -fno-pic -fno-stack-protector -DOLD_DEVICE -o old.o src/dummy.c
gcc -c -ffreestanding -fno-pic -fno-stack-protector              -o new.o src/dummy.c

cd old && ld -nostdlib -static -e _start -T sections.ld \
  --defsym=STACK_CORE0_SIZE=4096 --defsym=STACK_CORE1_SIZE=4096 \
  --defsym=CSA_CORE0_COUNT=64 --defsym=CSA_CORE1_COUNT=64 \
  -Map=old.map -o old.elf ../old.o

cd ../new && ld -nostdlib -static -e _start -T sections.ld \
  --defsym=STACK_CORE0_SIZE=8192 --defsym=STACK_CORE1_SIZE=8192 --defsym=STACK_CORE2_SIZE=4096 \
  --defsym=CSA_CORE0_COUNT=64 --defsym=CSA_CORE1_COUNT=64 --defsym=CSA_CORE2_COUNT=32 \
  -Map=new.map -o new.elf ../new.o
```

The committed maps are trimmed to output sections. Built with GNU ld 2.42 on an x86-64 host, so this checks script logic, not behavior on a target.

## Walkthrough

Run the checker three ways from this directory.

### 1. Old map against old declarations: passes

```
python ../../tools/check_layout.py old/firmware.map old/layout.toml
```

This is the baseline. Always start from a known-good state.

### 2. New map against the old declarations: fails

```
python ../../tools/check_layout.py new/firmware.map old/layout.toml
```

```
ERROR  .shared_mailbox: declared address 0x20000000, map places it at 0x20008000
ERROR  .stack_core0: declared 4096 (0x1000) bytes, map places 8192 (0x2000) bytes
ERROR  .stack_core1: declared 4096 (0x1000) bytes, map places 8192 (0x2000) bytes
```

This is what a half-migrated project looks like: the build moved on, a declaration did not. The mailbox line matters most. The linker is fine with the new address. A tool that still reads the old address will fail, and nothing in the build says so.

### 3. New map against updated declarations: passes

```
python ../../tools/check_layout.py new/firmware.map new/layout.toml
```

## What the checker did not tell you

In step 2 the checker said nothing about core 2. It only checks what you declared, and the old file never mentioned core 2. A new core, a new region, or a new reserved range does not show up as an error.

For those, use the migration checklist in [USER_GUIDE.md](../../docs/USER_GUIDE.md): diff the memory regions of old and new, list every value that encodes an address or a size, and make sure each has a declaration.

```
diff old/memory.ld new/memory.ld
```

## Exercise

1. Add a declaration for `.core2_data` to `new/layout.toml` and check it passes.
2. Link the new device with `STACK_CORE2_SIZE=29696` and change the core 2 stack declaration to 29696. The link succeeds. What does the checker say? (A region usage warning: `CORE2_LOCAL: 32000 of 32768 bytes used (97.7 percent)`. The layout is legal and has almost no room left.) Now try `STACK_CORE2_SIZE=32768`. Which tool stops you, and with what message? (The linker: `region 'CORE2_LOCAL' overflowed by 2304 bytes`.)
3. Set the mailbox declaration in `new/layout.toml` to the old address again and rerun. Confirm the error.
4. In a real project, where else might the mailbox address be written down? List every place. Each one is a stale-value risk.
