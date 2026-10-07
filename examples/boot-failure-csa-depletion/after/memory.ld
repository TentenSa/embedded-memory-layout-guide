/* Synthetic example. Invented device and addresses. */

MEMORY
{
  FLASH       (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
  RAM         (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
  CORE0_LOCAL (rwx) : ORIGIN = 0x30000000, LENGTH = 16K
  CORE1_LOCAL (rwx) : ORIGIN = 0x30100000, LENGTH = 16K
}
