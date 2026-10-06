/* Synthetic example. New device: 3 cores used, more flash and RAM.
 * The first 32 KB of RAM is reserved by the new boot flow and is not
 * a region here, so RAM now starts higher than on the old device.
 */

MEMORY
{
  FLASH       (rx)  : ORIGIN = 0x08000000, LENGTH = 1M
  RAM         (rwx) : ORIGIN = 0x20008000, LENGTH = 160K
  CORE0_LOCAL (rwx) : ORIGIN = 0x30000000, LENGTH = 32K
  CORE1_LOCAL (rwx) : ORIGIN = 0x30100000, LENGTH = 32K
  CORE2_LOCAL (rwx) : ORIGIN = 0x30200000, LENGTH = 32K
}
