/* Synthetic example. New device. Invented addresses.
 *
 * STACK_CORE0_SIZE, STACK_CORE1_SIZE, CSA_CORE0_COUNT and CSA_CORE1_COUNT
 * come from layout.toml through --defsym (the E2 step).
 * CORE2 symbols are new on this device.
 * There are no default values on purpose. If the build does not supply
 * a symbol, ld stops with "undefined symbol ... referenced in expression"
 * instead of silently using a stale number.
 */

INCLUDE memory.ld

SECTIONS
{
  /* Specific rules first. GNU ld uses the first matching rule. */

  /* Shared structure read by an external tool, first in RAM */
  .shared_mailbox (NOLOAD) : ALIGN(16)
  {
    *(.shared_mailbox)
  } > RAM

  .text : ALIGN(4)
  {
    *(.text.startup*)
    *(.text .text.*)
    *(.rodata .rodata.*)
  } > FLASH

  .data : ALIGN(4)
  {
    __data_start = .;
    *(.data .data.*)
    __data_end = .;
  } > RAM AT > FLASH
  __data_load = LOADADDR(.data);

  .bss (NOLOAD) : ALIGN(4)
  {
    __bss_start = .;
    *(.bss .bss.*) *(COMMON)
    __bss_end = .;
  } > RAM

  /* Core 0 local memory: CSA area, then stack, then core-local data */

  .csa_core0 (NOLOAD) : ALIGN(64)
  {
    __csa_core0_base = .;
    . += CSA_CORE0_COUNT * 64;
    __csa_core0_end = .;
  } > CORE0_LOCAL

  .stack_core0 (NOLOAD) : ALIGN(8)
  {
    __stack_core0_base = .;
    . += STACK_CORE0_SIZE;
    __stack_core0_top = .;
  } > CORE0_LOCAL

  .core0_data : ALIGN(4)
  {
    *(.core0_data .core0_data.*)
  } > CORE0_LOCAL

  /* Core 1 local memory */

  .csa_core1 (NOLOAD) : ALIGN(64)
  {
    __csa_core1_base = .;
    . += CSA_CORE1_COUNT * 64;
    __csa_core1_end = .;
  } > CORE1_LOCAL

  .stack_core1 (NOLOAD) : ALIGN(8)
  {
    __stack_core1_base = .;
    . += STACK_CORE1_SIZE;
    __stack_core1_top = .;
  } > CORE1_LOCAL

  .core1_data : ALIGN(4)
  {
    *(.core1_data .core1_data.*)
  } > CORE1_LOCAL

  /* Core 2 local memory (new on this device) */

  .csa_core2 (NOLOAD) : ALIGN(64)
  {
    __csa_core2_base = .;
    . += CSA_CORE2_COUNT * 64;
    __csa_core2_end = .;
  } > CORE2_LOCAL

  .stack_core2 (NOLOAD) : ALIGN(8)
  {
    __stack_core2_base = .;
    . += STACK_CORE2_SIZE;
    __stack_core2_top = .;
  } > CORE2_LOCAL

  .core2_data : ALIGN(4)
  {
    *(.core2_data .core2_data.*)
  } > CORE2_LOCAL
}
