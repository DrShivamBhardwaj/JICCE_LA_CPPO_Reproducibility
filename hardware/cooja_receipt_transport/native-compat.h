/* cooja-log.c uses host free(); Contiki's minimal stdlib.h omits it. */
#ifndef NATIVE_COMPAT_H_
#define NATIVE_COMPAT_H_
void free(void *);
#endif
