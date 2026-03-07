// Auto-generated from normal-distribution-histogram.gif
// Generated: 2026-03-07T12:49:55.358529
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


#define NORMAL_DISTRIBUTION_HISTOGRAM_FRAME_WIDTH   32
#define NORMAL_DISTRIBUTION_HISTOGRAM_FRAME_HEIGHT  32
#define NORMAL_DISTRIBUTION_HISTOGRAM_BYTES_PER_ROW ((NORMAL_DISTRIBUTION_HISTOGRAM_FRAME_WIDTH + 7) / 8)
#define NORMAL_DISTRIBUTION_HISTOGRAM_FRAME_COUNT   18
#define NORMAL_DISTRIBUTION_HISTOGRAM_BYTES_PER_FRAME 128

// Uso: row = offset / BYTES_PER_ROW; col_byte = offset % BYTES_PER_ROW; buffer[offset] = value;

// Frame 0 (completo)
const uint8_t normal_distribution_histogram_frame_0[] PROGMEM = {
    0xC0, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00,
    0xC0, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x00, 0x00,
    0xC0, 0x00, 0x00, 0x00, 0xC0, 0x03, 0xC0, 0x00, 0xC0, 0x0F, 0xF0, 0x00, 0xC0, 0x1C, 0x38, 0x00,
    0xC0, 0x18, 0x18, 0x00, 0xC0, 0x38, 0x1C, 0x00, 0xC0, 0x30, 0x0C, 0x00, 0xC0, 0x30, 0x0C, 0x00,
    0xC0, 0x70, 0x0E, 0x00, 0xC0, 0x60, 0x06, 0x00, 0xC0, 0x60, 0x06, 0x00, 0xC0, 0x60, 0x06, 0x00,
    0xC0, 0xE0, 0x07, 0x00, 0xC0, 0xC0, 0x03, 0x00, 0xC0, 0xC0, 0x03, 0x00, 0xC0, 0xC0, 0x03, 0x00,
    0xC1, 0xC0, 0x03, 0x80, 0xC1, 0x80, 0x01, 0x80, 0xC1, 0x80, 0x01, 0x80, 0xC3, 0x00, 0x00, 0xC0,
    0xC7, 0x00, 0x00, 0xE0, 0xCE, 0x00, 0x00, 0x70, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
};

// Frame 1 diff: 0 bytes
const uint16_t normal_distribution_histogram_diff_1_count = 0;
const uint16_t normal_distribution_histogram_diff_1_offsets[] PROGMEM = {
};
const uint8_t normal_distribution_histogram_diff_1_values[] PROGMEM = {
};

// Frame 2 diff: 1 bytes
const uint16_t normal_distribution_histogram_diff_2_count = 1;
const uint16_t normal_distribution_histogram_diff_2_offsets[] PROGMEM = {
    116
};
const uint8_t normal_distribution_histogram_diff_2_values[] PROGMEM = {
    0xC6
};

// Frame 3 diff: 9 bytes
const uint16_t normal_distribution_histogram_diff_3_count = 9;
const uint16_t normal_distribution_histogram_diff_3_offsets[] PROGMEM = {
    96, 97, 100, 101, 104, 105, 108, 112, 116
};
const uint8_t normal_distribution_histogram_diff_3_values[] PROGMEM = {
    0xC0, 0x00, 0xC0, 0x00, 0xC0, 0x00, 0xC0, 0xC0, 0xC0
};

// Frame 4 diff: 12 bytes
const uint16_t normal_distribution_histogram_diff_4_count = 12;
const uint16_t normal_distribution_histogram_diff_4_offsets[] PROGMEM = {
    45, 53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93
};
const uint8_t normal_distribution_histogram_diff_4_values[] PROGMEM = {
    0x0C, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 5 diff: 10 bytes
const uint16_t normal_distribution_histogram_diff_5_count = 10;
const uint16_t normal_distribution_histogram_diff_5_offsets[] PROGMEM = {
    37, 38, 41, 42, 45, 46, 49, 50, 53, 54
};
const uint8_t normal_distribution_histogram_diff_5_values[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C
};

// Frame 6 diff: 12 bytes
const uint16_t normal_distribution_histogram_diff_6_count = 12;
const uint16_t normal_distribution_histogram_diff_6_offsets[] PROGMEM = {
    54, 58, 62, 66, 70, 74, 78, 82, 86, 90, 94, 98
};
const uint8_t normal_distribution_histogram_diff_6_values[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01
};

// Frame 7 diff: 9 bytes
const uint16_t normal_distribution_histogram_diff_7_count = 9;
const uint16_t normal_distribution_histogram_diff_7_offsets[] PROGMEM = {
    98, 99, 102, 103, 106, 107, 111, 115, 119
};
const uint8_t normal_distribution_histogram_diff_7_values[] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// Frame 8 diff: 0 bytes
const uint16_t normal_distribution_histogram_diff_8_count = 0;
const uint16_t normal_distribution_histogram_diff_8_offsets[] PROGMEM = {
};
const uint8_t normal_distribution_histogram_diff_8_values[] PROGMEM = {
};

// Frame 9 diff: 0 bytes
const uint16_t normal_distribution_histogram_diff_9_count = 0;
const uint16_t normal_distribution_histogram_diff_9_offsets[] PROGMEM = {
};
const uint8_t normal_distribution_histogram_diff_9_values[] PROGMEM = {
};

// Frame 10 diff: 9 bytes
const uint16_t normal_distribution_histogram_diff_10_count = 9;
const uint16_t normal_distribution_histogram_diff_10_offsets[] PROGMEM = {
    96, 97, 100, 101, 104, 105, 108, 112, 116
};
const uint8_t normal_distribution_histogram_diff_10_values[] PROGMEM = {
    0xC1, 0x80, 0xC1, 0x80, 0xC1, 0x80, 0xC3, 0xC7, 0xCE
};

// Frame 11 diff: 12 bytes
const uint16_t normal_distribution_histogram_diff_11_count = 12;
const uint16_t normal_distribution_histogram_diff_11_offsets[] PROGMEM = {
    53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93, 97
};
const uint8_t normal_distribution_histogram_diff_11_values[] PROGMEM = {
    0x30, 0x30, 0x30, 0x70, 0x60, 0x60, 0x60, 0xE0, 0xC0, 0xC0, 0xC0, 0xC0
};

// Frame 12 diff: 10 bytes
const uint16_t normal_distribution_histogram_diff_12_count = 10;
const uint16_t normal_distribution_histogram_diff_12_offsets[] PROGMEM = {
    37, 38, 41, 42, 45, 46, 49, 50, 53, 54
};
const uint8_t normal_distribution_histogram_diff_12_values[] PROGMEM = {
    0x03, 0xC0, 0x0F, 0xF0, 0x1C, 0x30, 0x18, 0x18, 0x38, 0x18
};

// Frame 13 diff: 12 bytes
const uint16_t normal_distribution_histogram_diff_13_count = 12;
const uint16_t normal_distribution_histogram_diff_13_offsets[] PROGMEM = {
    46, 54, 58, 62, 66, 70, 74, 78, 82, 86, 90, 94
};
const uint8_t normal_distribution_histogram_diff_13_values[] PROGMEM = {
    0x38, 0x1C, 0x0C, 0x0C, 0x0E, 0x06, 0x06, 0x06, 0x07, 0x03, 0x03, 0x03
};

// Frame 14 diff: 9 bytes
const uint16_t normal_distribution_histogram_diff_14_count = 9;
const uint16_t normal_distribution_histogram_diff_14_offsets[] PROGMEM = {
    98, 99, 102, 103, 106, 107, 111, 115, 119
};
const uint8_t normal_distribution_histogram_diff_14_values[] PROGMEM = {
    0x03, 0x80, 0x01, 0x80, 0x01, 0x80, 0xC0, 0xE0, 0x60
};

// Frame 15 diff: 1 bytes
const uint16_t normal_distribution_histogram_diff_15_count = 1;
const uint16_t normal_distribution_histogram_diff_15_offsets[] PROGMEM = {
    119
};
const uint8_t normal_distribution_histogram_diff_15_values[] PROGMEM = {
    0x70
};

// Frame 16 diff: 0 bytes
const uint16_t normal_distribution_histogram_diff_16_count = 0;
const uint16_t normal_distribution_histogram_diff_16_offsets[] PROGMEM = {
};
const uint8_t normal_distribution_histogram_diff_16_values[] PROGMEM = {
};

// Frame 17 diff: 0 bytes
const uint16_t normal_distribution_histogram_diff_17_count = 0;
const uint16_t normal_distribution_histogram_diff_17_offsets[] PROGMEM = {
};
const uint8_t normal_distribution_histogram_diff_17_values[] PROGMEM = {
};

// Punteros por frame (índice 0 = frame 1, 1 = frame 2, ...)
const uint16_t* const normal_distribution_histogram_diff_offsets[] PROGMEM = {
    normal_distribution_histogram_diff_1_offsets,
    normal_distribution_histogram_diff_2_offsets,
    normal_distribution_histogram_diff_3_offsets,
    normal_distribution_histogram_diff_4_offsets,
    normal_distribution_histogram_diff_5_offsets,
    normal_distribution_histogram_diff_6_offsets,
    normal_distribution_histogram_diff_7_offsets,
    normal_distribution_histogram_diff_8_offsets,
    normal_distribution_histogram_diff_9_offsets,
    normal_distribution_histogram_diff_10_offsets,
    normal_distribution_histogram_diff_11_offsets,
    normal_distribution_histogram_diff_12_offsets,
    normal_distribution_histogram_diff_13_offsets,
    normal_distribution_histogram_diff_14_offsets,
    normal_distribution_histogram_diff_15_offsets,
    normal_distribution_histogram_diff_16_offsets,
    normal_distribution_histogram_diff_17_offsets
};
const uint8_t* const normal_distribution_histogram_diff_values[] PROGMEM = {
    normal_distribution_histogram_diff_1_values,
    normal_distribution_histogram_diff_2_values,
    normal_distribution_histogram_diff_3_values,
    normal_distribution_histogram_diff_4_values,
    normal_distribution_histogram_diff_5_values,
    normal_distribution_histogram_diff_6_values,
    normal_distribution_histogram_diff_7_values,
    normal_distribution_histogram_diff_8_values,
    normal_distribution_histogram_diff_9_values,
    normal_distribution_histogram_diff_10_values,
    normal_distribution_histogram_diff_11_values,
    normal_distribution_histogram_diff_12_values,
    normal_distribution_histogram_diff_13_values,
    normal_distribution_histogram_diff_14_values,
    normal_distribution_histogram_diff_15_values,
    normal_distribution_histogram_diff_16_values,
    normal_distribution_histogram_diff_17_values
};
const uint16_t normal_distribution_histogram_diff_counts[] PROGMEM = { 0, 1, 9, 12, 10, 12, 9, 0, 0, 9, 12, 10, 12, 9, 1, 0, 0 };

uint16_t normal_distribution_histogram_frame_count = 18;
uint16_t normal_distribution_histogram_frame_width = 32;
uint16_t normal_distribution_histogram_frame_height = 32;
uint16_t normal_distribution_histogram_bytes_per_frame = 128;
