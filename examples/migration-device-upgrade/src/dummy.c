/* Synthetic placeholder code and data, only so the linker has input sections. */
int g_init = 5;
int g_bss[100];

__attribute__((section(".shared_mailbox"))) int mailbox[16];
__attribute__((section(".core0_data"))) int c0[300];
__attribute__((section(".core1_data"))) int c1[100];
#ifndef OLD_DEVICE
__attribute__((section(".core2_data"))) int c2[64];
#endif

int f(int x) { return x + g_init + g_bss[0] + mailbox[0] + c0[0] + c1[0]; }
void _start(void) { f(1); for (;;) ; }
