// Auto-generated from temperature.gif
// Generated: 2026-03-07T13:14:04.592623
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


#define TEMPERATURE_FRAME_WIDTH   32
#define TEMPERATURE_FRAME_HEIGHT  32
#define TEMPERATURE_BYTES_PER_ROW ((TEMPERATURE_FRAME_WIDTH + 7) / 8)
#define TEMPERATURE_FRAME_COUNT   23
#define TEMPERATURE_BYTES_PER_FRAME 128

// Uso: row = offset / BYTES_PER_ROW; col_byte = offset % BYTES_PER_ROW; buffer[offset] = value;

// Frame 0 (completo)
const uint8_t temperature_frame_0[] PROGMEM = {
    0x00, 0x03, 0xC0, 0x00, 0x00, 0x04, 0x20, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x10, 0x00,
    0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x0F, 0xFC, 0x00, 0x00, 0x08, 0x10, 0x00,
    0x00, 0x08, 0x1C, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x1C, 0x00,
    0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x08, 0x1C, 0x00, 0x00, 0x08, 0x10, 0x00,
    0x00, 0x08, 0x1C, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x30, 0x0C, 0x00,
    0x00, 0x20, 0x04, 0x00, 0x00, 0x40, 0x02, 0x00, 0x00, 0x40, 0x02, 0x00, 0x00, 0xC0, 0x03, 0x00,
    0x00, 0xC0, 0x03, 0x00, 0x00, 0x40, 0x02, 0x00, 0x00, 0x40, 0x02, 0x00, 0x00, 0x40, 0x02, 0x00,
    0x00, 0x20, 0x04, 0x00, 0x00, 0x10, 0x08, 0x00, 0x00, 0x0C, 0x30, 0x00, 0x00, 0x03, 0xC0, 0x00
};

// Frame 1 diff: 0 bytes
const uint16_t temperature_diff_1_count = 0;
const uint16_t temperature_diff_1_offsets[] PROGMEM = {
};
const uint8_t temperature_diff_1_values[] PROGMEM = {
};

// Frame 2 diff: 13 bytes
const uint16_t temperature_diff_2_count = 13;
const uint16_t temperature_diff_2_offsets[] PROGMEM = {
    6, 10, 21, 22, 25, 26, 82, 93, 94, 97, 98, 102,
    118
};
const uint8_t temperature_diff_2_values[] PROGMEM = {
    0x60, 0x20, 0x0F, 0xF0, 0x0C, 0x3C, 0x06, 0x40, 0x01, 0x40, 0x01, 0x01, 0x0C
};

// Frame 3 diff: 14 bytes
const uint16_t temperature_diff_3_count = 14;
const uint16_t temperature_diff_3_offsets[] PROGMEM = {
    14, 17, 18, 21, 22, 25, 30, 54, 58, 78, 90, 109,
    122, 126
};
const uint8_t temperature_diff_3_values[] PROGMEM = {
    0x20, 0x09, 0xA0, 0x0E, 0x70, 0x08, 0x20, 0x14, 0x10, 0x04, 0x01, 0x60, 0x38, 0xE0
};

// Frame 4 diff: 12 bytes
const uint16_t temperature_diff_4_count = 12;
const uint16_t temperature_diff_4_offsets[] PROGMEM = {
    5, 17, 18, 21, 22, 34, 54, 73, 77, 82, 106, 114
};
const uint8_t temperature_diff_4_values[] PROGMEM = {
    0x0C, 0x0F, 0xE0, 0x08, 0x20, 0x3C, 0x1C, 0x08, 0x10, 0x02, 0x03, 0x06
};

// Frame 5 diff: 13 bytes
const uint16_t temperature_diff_5_count = 13;
const uint16_t temperature_diff_5_offsets[] PROGMEM = {
    5, 17, 18, 22, 26, 33, 34, 54, 73, 77, 82, 106,
    114
};
const uint8_t temperature_diff_5_values[] PROGMEM = {
    0x04, 0x08, 0x20, 0x30, 0x1C, 0x0F, 0xFC, 0x14, 0x18, 0x30, 0x06, 0x02, 0x04
};

// Frame 6 diff: 16 bytes
const uint16_t temperature_diff_6_count = 16;
const uint16_t temperature_diff_6_offsets[] PROGMEM = {
    14, 18, 22, 30, 33, 34, 54, 57, 58, 61, 62, 78,
    90, 109, 122, 126
};
const uint8_t temperature_diff_6_values[] PROGMEM = {
    0x10, 0x10, 0x10, 0x10, 0x08, 0x1C, 0x10, 0x0C, 0x3C, 0x0F, 0xF0, 0x0C, 0x02, 0x40, 0x30, 0xC0
};

// Frame 7 diff: 17 bytes
const uint16_t temperature_diff_7_count = 17;
const uint16_t temperature_diff_7_offsets[] PROGMEM = {
    6, 10, 57, 58, 61, 62, 73, 74, 77, 78, 82, 93,
    94, 97, 98, 102, 118
};
const uint8_t temperature_diff_7_values[] PROGMEM = {
    0x20, 0x10, 0x08, 0x1C, 0x08, 0x10, 0x1E, 0x78, 0x33, 0x8C, 0x04, 0xC0, 0x03, 0xC0, 0x03, 0x02,
    0x08
};

// Frame 8 diff: 6 bytes
const uint16_t temperature_diff_8_count = 6;
const uint16_t temperature_diff_8_offsets[] PROGMEM = {
    69, 70, 73, 74, 77, 78
};
const uint8_t temperature_diff_8_values[] PROGMEM = {
    0x0C, 0x30, 0x1F, 0xF8, 0x30, 0x0C
};

// Frame 9 diff: 5 bytes
const uint16_t temperature_diff_9_count = 5;
const uint16_t temperature_diff_9_offsets[] PROGMEM = {
    65, 69, 70, 73, 74
};
const uint8_t temperature_diff_9_values[] PROGMEM = {
    0x0C, 0x0F, 0xF0, 0x18, 0x18
};

// Frame 10 diff: 4 bytes
const uint16_t temperature_diff_10_count = 4;
const uint16_t temperature_diff_10_offsets[] PROGMEM = {
    65, 66, 69, 70
};
const uint8_t temperature_diff_10_values[] PROGMEM = {
    0x0E, 0x7C, 0x0D, 0xB0
};

// Frame 11 diff: 4 bytes
const uint16_t temperature_diff_11_count = 4;
const uint16_t temperature_diff_11_offsets[] PROGMEM = {
    65, 66, 69, 70
};
const uint8_t temperature_diff_11_values[] PROGMEM = {
    0x0F, 0xFC, 0x0C, 0x10
};

// Frame 12 diff: 1 bytes
const uint16_t temperature_diff_12_count = 1;
const uint16_t temperature_diff_12_offsets[] PROGMEM = {
    70
};
const uint8_t temperature_diff_12_values[] PROGMEM = {
    0x30
};

// Frame 13 diff: 15 bytes
const uint16_t temperature_diff_13_count = 15;
const uint16_t temperature_diff_13_offsets[] PROGMEM = {
    5, 9, 38, 65, 66, 69, 70, 74, 81, 93, 94, 97,
    98, 101, 117
};
const uint8_t temperature_diff_13_values[] PROGMEM = {
    0x06, 0x04, 0x1C, 0x0C, 0x3C, 0x0F, 0xF0, 0x10, 0x60, 0x80, 0x02, 0x80, 0x02, 0x80, 0x30
};

// Frame 14 diff: 17 bytes
const uint16_t temperature_diff_14_count = 17;
const uint16_t temperature_diff_14_offsets[] PROGMEM = {
    13, 17, 21, 25, 29, 34, 65, 66, 69, 70, 73, 74,
    77, 89, 110, 121, 125
};
const uint8_t temperature_diff_14_values[] PROGMEM = {
    0x04, 0x04, 0x04, 0x04, 0x04, 0x10, 0x08, 0x1C, 0x0E, 0x70, 0x1B, 0xD0, 0x20, 0x80, 0x06, 0x1C,
    0x07
};

// Frame 15 diff: 11 bytes
const uint16_t temperature_diff_15_count = 11;
const uint16_t temperature_diff_15_offsets[] PROGMEM = {
    6, 33, 37, 69, 70, 73, 74, 78, 81, 105, 113
};
const uint8_t temperature_diff_15_values[] PROGMEM = {
    0x30, 0x04, 0x00, 0x0C, 0x30, 0x1F, 0xF0, 0x08, 0x40, 0xC0, 0x60
};

// Frame 16 diff: 14 bytes
const uint16_t temperature_diff_16_count = 14;
const uint16_t temperature_diff_16_offsets[] PROGMEM = {
    6, 33, 37, 57, 58, 62, 69, 70, 73, 74, 78, 81,
    105, 113
};
const uint8_t temperature_diff_16_values[] PROGMEM = {
    0x20, 0x08, 0x08, 0x0F, 0xFC, 0x30, 0x08, 0x10, 0x18, 0x10, 0x0C, 0x60, 0x40, 0x20
};

// Frame 17 diff: 16 bytes
const uint16_t temperature_diff_17_count = 16;
const uint16_t temperature_diff_17_offsets[] PROGMEM = {
    13, 17, 21, 25, 29, 30, 33, 34, 57, 58, 62, 77,
    89, 110, 121, 125
};
const uint8_t temperature_diff_17_values[] PROGMEM = {
    0x08, 0x08, 0x08, 0x08, 0x0F, 0xF0, 0x0C, 0x3C, 0x08, 0x1C, 0x10, 0x30, 0x40, 0x02, 0x0C, 0x03
};

// Frame 18 diff: 19 bytes
const uint16_t temperature_diff_18_count = 19;
const uint16_t temperature_diff_18_offsets[] PROGMEM = {
    5, 9, 13, 14, 17, 18, 29, 30, 33, 34, 38, 74,
    81, 93, 94, 97, 98, 101, 117
};
const uint8_t temperature_diff_18_values[] PROGMEM = {
    0x04, 0x08, 0x09, 0x90, 0x0E, 0x70, 0x08, 0x10, 0x08, 0x1C, 0x10, 0x18, 0x20, 0xC0, 0x03, 0xC0,
    0x03, 0x40, 0x10
};

// Frame 19 diff: 4 bytes
const uint16_t temperature_diff_19_count = 4;
const uint16_t temperature_diff_19_offsets[] PROGMEM = {
    13, 14, 17, 18
};
const uint8_t temperature_diff_19_values[] PROGMEM = {
    0x0F, 0xF0, 0x0C, 0x30
};

// Frame 20 diff: 6 bytes
const uint16_t temperature_diff_20_count = 6;
const uint16_t temperature_diff_20_offsets[] PROGMEM = {
    13, 14, 17, 18, 21, 22
};
const uint8_t temperature_diff_20_values[] PROGMEM = {
    0x08, 0x10, 0x09, 0x90, 0x0E, 0xF0
};

// Frame 21 diff: 6 bytes
const uint16_t temperature_diff_21_count = 6;
const uint16_t temperature_diff_21_offsets[] PROGMEM = {
    17, 18, 21, 22, 25, 26
};
const uint8_t temperature_diff_21_values[] PROGMEM = {
    0x08, 0x10, 0x0D, 0xB0, 0x0E, 0x7C
};

// Frame 22 diff: 4 bytes
const uint16_t temperature_diff_22_count = 4;
const uint16_t temperature_diff_22_offsets[] PROGMEM = {
    21, 22, 25, 26
};
const uint8_t temperature_diff_22_values[] PROGMEM = {
    0x08, 0x10, 0x0F, 0xFC
};

// Punteros por frame (índice 0 = frame 1, 1 = frame 2, ...)
const uint16_t* const temperature_diff_offsets[] PROGMEM = {
    temperature_diff_1_offsets,
    temperature_diff_2_offsets,
    temperature_diff_3_offsets,
    temperature_diff_4_offsets,
    temperature_diff_5_offsets,
    temperature_diff_6_offsets,
    temperature_diff_7_offsets,
    temperature_diff_8_offsets,
    temperature_diff_9_offsets,
    temperature_diff_10_offsets,
    temperature_diff_11_offsets,
    temperature_diff_12_offsets,
    temperature_diff_13_offsets,
    temperature_diff_14_offsets,
    temperature_diff_15_offsets,
    temperature_diff_16_offsets,
    temperature_diff_17_offsets,
    temperature_diff_18_offsets,
    temperature_diff_19_offsets,
    temperature_diff_20_offsets,
    temperature_diff_21_offsets,
    temperature_diff_22_offsets
};
const uint8_t* const temperature_diff_values[] PROGMEM = {
    temperature_diff_1_values,
    temperature_diff_2_values,
    temperature_diff_3_values,
    temperature_diff_4_values,
    temperature_diff_5_values,
    temperature_diff_6_values,
    temperature_diff_7_values,
    temperature_diff_8_values,
    temperature_diff_9_values,
    temperature_diff_10_values,
    temperature_diff_11_values,
    temperature_diff_12_values,
    temperature_diff_13_values,
    temperature_diff_14_values,
    temperature_diff_15_values,
    temperature_diff_16_values,
    temperature_diff_17_values,
    temperature_diff_18_values,
    temperature_diff_19_values,
    temperature_diff_20_values,
    temperature_diff_21_values,
    temperature_diff_22_values
};
const uint16_t temperature_diff_counts[] PROGMEM = { 0, 13, 14, 12, 13, 16, 17, 6, 5, 4, 4, 1, 15, 17, 11, 14, 16, 19, 4, 6, 6, 4 };

uint16_t temperature_frame_count = 23;
uint16_t temperature_frame_width = 32;
uint16_t temperature_frame_height = 32;
uint16_t temperature_bytes_per_frame = 128;
