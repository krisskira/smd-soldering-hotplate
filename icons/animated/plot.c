// Auto-generated from plot.gif
// Generated: 2026-03-07T12:32:23.118850
// Modo DIFF: frame 0 completo + solo bytes que cambiaron. Formato compatible ST7920 128x64.
// STORE_IN_FLASH: Arduino=PROGMEM; C estándar=PROGMEM vacío.

#include <stdint.h>

// Compatible Arduino (AVR) y C estándar.
#ifdef __AVR__
  #include <avr/pgmspace.h>
#else
  #define PROGMEM
  #define pgm_read_byte(addr)  (*(const uint8_t *)(addr))
  #define pgm_read_word(addr) (*(const uint16_t *)(addr))
#endif


#define PLOT_FRAME_WIDTH   32
#define PLOT_FRAME_HEIGHT  32
#define PLOT_BYTES_PER_ROW ((PLOT_FRAME_WIDTH + 7) / 8)
#define PLOT_FRAME_COUNT   19
#define PLOT_BYTES_PER_FRAME 128

// Uso: row = offset / BYTES_PER_ROW; col_byte = offset % BYTES_PER_ROW; buffer[offset] = value;

// Frame 0 (completo)
const uint8_t plot_frame_0[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x00, 0x06,
    0xF0, 0x00, 0x00, 0x0E, 0x98, 0x00, 0x00, 0x18, 0x8C, 0x00, 0x00, 0x30, 0x86, 0x00, 0x00, 0x20,
    0x86, 0x00, 0x00, 0x60, 0x83, 0x00, 0x00, 0x40, 0x83, 0x00, 0x00, 0xC0, 0x81, 0x00, 0x00, 0xC0,
    0x81, 0x80, 0x00, 0x80, 0x81, 0x80, 0x01, 0x80, 0x80, 0x80, 0x01, 0x80, 0xFE, 0xDF, 0xFD, 0x3F,
    0xFE, 0xDF, 0xF9, 0x7F, 0x80, 0x40, 0x03, 0x00, 0x80, 0x60, 0x03, 0x00, 0x80, 0x60, 0x02, 0x00,
    0x80, 0x30, 0x06, 0x00, 0x80, 0x30, 0x06, 0x00, 0x80, 0x10, 0x04, 0x00, 0x80, 0x18, 0x0C, 0x00,
    0x80, 0x18, 0x0C, 0x00, 0x80, 0x0C, 0x18, 0x00, 0x80, 0x06, 0x30, 0x00, 0x80, 0x03, 0xF0, 0x00,
    0x80, 0x01, 0xC0, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 1 diff: 0 bytes
const uint16_t plot_diff_1_count = 0;
const uint16_t plot_diff_1_offsets[] PROGMEM = {
};
const uint8_t plot_diff_1_values[] PROGMEM = {
};

// Frame 2 diff: 4 bytes
const uint16_t plot_diff_2_count = 4;
const uint16_t plot_diff_2_offsets[] PROGMEM = {
    12, 16, 20, 24
};
const uint8_t plot_diff_2_values[] PROGMEM = {
    0x80, 0x80, 0x80, 0x84
};

// Frame 3 diff: 9 bytes
const uint16_t plot_diff_3_count = 9;
const uint16_t plot_diff_3_offsets[] PROGMEM = {
    24, 28, 32, 36, 40, 44, 48, 49, 52
};
const uint8_t plot_diff_3_values[] PROGMEM = {
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x00, 0x80
};

// Frame 4 diff: 12 bytes
const uint16_t plot_diff_4_count = 12;
const uint16_t plot_diff_4_offsets[] PROGMEM = {
    53, 57, 60, 61, 64, 65, 69, 73, 77, 81, 85, 89
};
const uint8_t plot_diff_4_values[] PROGMEM = {
    0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 5 diff: 10 bytes
const uint16_t plot_diff_5_count = 10;
const uint16_t plot_diff_5_offsets[] PROGMEM = {
    93, 97, 101, 102, 105, 106, 109, 110, 113, 114
};
const uint8_t plot_diff_5_values[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 6 diff: 16 bytes
const uint16_t plot_diff_6_count = 16;
const uint16_t plot_diff_6_offsets[] PROGMEM = {
    54, 55, 58, 59, 62, 63, 66, 67, 70, 74, 78, 82,
    86, 90, 94, 98
};
const uint8_t plot_diff_6_values[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 7 diff: 8 bytes
const uint16_t plot_diff_7_count = 8;
const uint16_t plot_diff_7_offsets[] PROGMEM = {
    23, 27, 31, 35, 39, 43, 47, 51
};
const uint8_t plot_diff_7_values[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 8 diff: 2 bytes
const uint16_t plot_diff_8_count = 2;
const uint16_t plot_diff_8_offsets[] PROGMEM = {
    15, 19
};
const uint8_t plot_diff_8_values[] PROGMEM = {
    0x00, 0x00
};

// Frame 9 diff: 2 bytes
const uint16_t plot_diff_9_count = 2;
const uint16_t plot_diff_9_offsets[] PROGMEM = {
    12, 16
};
const uint8_t plot_diff_9_values[] PROGMEM = {
    0xE0, 0xF0
};

// Frame 10 diff: 8 bytes
const uint16_t plot_diff_10_count = 8;
const uint16_t plot_diff_10_offsets[] PROGMEM = {
    20, 24, 28, 32, 36, 40, 44, 48
};
const uint8_t plot_diff_10_values[] PROGMEM = {
    0x98, 0x8C, 0x86, 0x86, 0x83, 0x83, 0x81, 0x81
};

// Frame 11 diff: 16 bytes
const uint16_t plot_diff_11_count = 16;
const uint16_t plot_diff_11_offsets[] PROGMEM = {
    49, 52, 53, 57, 60, 61, 64, 65, 69, 73, 77, 81,
    85, 89, 93, 97
};
const uint8_t plot_diff_11_values[] PROGMEM = {
    0x80, 0x81, 0x80, 0x80, 0xFE, 0xDF, 0xFE, 0xDF, 0x40, 0x60, 0x60, 0x30, 0x30, 0x10, 0x18, 0x18
};

// Frame 12 diff: 10 bytes
const uint16_t plot_diff_12_count = 10;
const uint16_t plot_diff_12_offsets[] PROGMEM = {
    94, 98, 101, 102, 105, 106, 109, 110, 113, 114
};
const uint8_t plot_diff_12_values[] PROGMEM = {
    0x0C, 0x0C, 0x0C, 0x18, 0x06, 0x38, 0x03, 0xF0, 0x01, 0xC0
};

// Frame 13 diff: 15 bytes
const uint16_t plot_diff_13_count = 15;
const uint16_t plot_diff_13_offsets[] PROGMEM = {
    54, 55, 58, 59, 62, 63, 66, 67, 70, 74, 78, 82,
    86, 90, 106
};
const uint8_t plot_diff_13_values[] PROGMEM = {
    0x01, 0x80, 0x01, 0x80, 0xFD, 0x3F, 0xF9, 0x7F, 0x03, 0x03, 0x02, 0x06, 0x06, 0x04, 0x30
};

// Frame 14 diff: 7 bytes
const uint16_t plot_diff_14_count = 7;
const uint16_t plot_diff_14_offsets[] PROGMEM = {
    27, 31, 35, 39, 43, 47, 51
};
const uint8_t plot_diff_14_values[] PROGMEM = {
    0x30, 0x30, 0x60, 0x40, 0xC0, 0xC0, 0x80
};

// Frame 15 diff: 4 bytes
const uint16_t plot_diff_15_count = 4;
const uint16_t plot_diff_15_offsets[] PROGMEM = {
    15, 19, 23, 31
};
const uint8_t plot_diff_15_values[] PROGMEM = {
    0x04, 0x0C, 0x18, 0x20
};

// Frame 16 diff: 2 bytes
const uint16_t plot_diff_16_count = 2;
const uint16_t plot_diff_16_offsets[] PROGMEM = {
    15, 19
};
const uint8_t plot_diff_16_values[] PROGMEM = {
    0x06, 0x0E
};

// Frame 17 diff: 0 bytes
const uint16_t plot_diff_17_count = 0;
const uint16_t plot_diff_17_offsets[] PROGMEM = {
};
const uint8_t plot_diff_17_values[] PROGMEM = {
};

// Frame 18 diff: 0 bytes
const uint16_t plot_diff_18_count = 0;
const uint16_t plot_diff_18_offsets[] PROGMEM = {
};
const uint8_t plot_diff_18_values[] PROGMEM = {
};

// Punteros por frame (índice 0 = frame 1, 1 = frame 2, ...)
const uint16_t* const plot_diff_offsets[] PROGMEM = {
    plot_diff_1_offsets,
    plot_diff_2_offsets,
    plot_diff_3_offsets,
    plot_diff_4_offsets,
    plot_diff_5_offsets,
    plot_diff_6_offsets,
    plot_diff_7_offsets,
    plot_diff_8_offsets,
    plot_diff_9_offsets,
    plot_diff_10_offsets,
    plot_diff_11_offsets,
    plot_diff_12_offsets,
    plot_diff_13_offsets,
    plot_diff_14_offsets,
    plot_diff_15_offsets,
    plot_diff_16_offsets,
    plot_diff_17_offsets,
    plot_diff_18_offsets
};
const uint8_t* const plot_diff_values[] PROGMEM = {
    plot_diff_1_values,
    plot_diff_2_values,
    plot_diff_3_values,
    plot_diff_4_values,
    plot_diff_5_values,
    plot_diff_6_values,
    plot_diff_7_values,
    plot_diff_8_values,
    plot_diff_9_values,
    plot_diff_10_values,
    plot_diff_11_values,
    plot_diff_12_values,
    plot_diff_13_values,
    plot_diff_14_values,
    plot_diff_15_values,
    plot_diff_16_values,
    plot_diff_17_values,
    plot_diff_18_values
};
const uint16_t plot_diff_counts[] PROGMEM = { 0, 4, 9, 12, 10, 16, 8, 2, 2, 8, 16, 10, 15, 7, 4, 2, 0, 0 };

uint16_t plot_frame_count = 19;
uint16_t plot_frame_width = 32;
uint16_t plot_frame_height = 32;
uint16_t plot_bytes_per_frame = 128;
