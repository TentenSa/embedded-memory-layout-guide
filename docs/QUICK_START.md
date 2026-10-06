# Quick Start

Five minutes. You need a linker script, a map file from a recent build, and whatever configuration drives your stack and region sizes.

## The idea

A layout value is trusted only when each stage agrees:

```
E1 source  ->  E2 build input  ->  E3 map file  ->  E4 runtime
"stack=4K"     "-Wl,--defsym"      ".stack_core0      "SP at main
in config      or generated .h     at 0x70001000      was 0x70001e40"
                                   size 0x1000"
```

Aim for E3 on every design value. Get E4 for anything involved in a failure.

## Worked check: is the core 0 stack really 4 KB?

1. E1. Find the declaration.
   ```
   grep -rn "STACK_CORE0" config/ linker/
   ```
2. E2. Find the same value in generated or preprocessed input.
   ```
   grep -rn "STACK_CORE0" build/generated/
   ```
3. E3. Find the placement in the map file.
   ```
   grep -n "stack_core0" build/firmware.map
   ```
   Check the address is inside the intended region and the size matches E1.
4. E4. Stop at `main`, read the stack pointer, compute used = top minus SP. Repeat after the worst-case interrupt load you can generate.

If E1 and E3 disagree, you have found a stale or overridden value. Stop there and investigate before sizing anything.

Steps 1 to 3 can be automated for declared sizes with [`tools/check_layout.py`](../tools/check_layout.py). Put your expectations in a TOML file (see the [example](../examples/dualcore-baseline/config/layout.toml)) and run it after every link.

## Which mode

| Question | Mode |
|---|---|
| What should the sizes be? | 1 Design |
| Why does it trap, hang, or read the wrong address? | 2 Investigate |
| We are moving to another derivative or toolchain | 3 Migrate |
| What does this linker message mean? | 4 Decode |
| Is this layout safe to release? | 5 Audit |

Details are in [USER_GUIDE.md](USER_GUIDE.md).

## Rules that save time

1. Do not copy sizes from another project. Use them as hints, then derive your own.
2. When several things are wrong, change one, rebuild, test, then change the next.
3. Record the reason next to each value, not only the value.
4. A comment saying a value was validated is not evidence. A map file line is.
