#ifndef HOST_PGMSPACE_H
#define HOST_PGMSPACE_H

#define PROGMEM
#define PGM_P const char *
#define PSTR(s) (s)
#define pgm_read_byte(p) (*(const unsigned char *)(p))
/* En el host los punteros son de 64 bits: se lee el elemento con su tipo. */
#define pgm_read_word(p) (*(p))
#define pgm_read_ptr(p) (*(p))

#endif
