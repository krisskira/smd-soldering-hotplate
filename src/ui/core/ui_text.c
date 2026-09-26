#include "ui_text.h"

uint8_t ui_str_len(const char *s)
{
    uint8_t n = 0;
    while (s[n])
        n++;
    return n;
}

void ui_line_clear(char *buf)
{
    for (uint8_t i = 0; i < LINE_LEN; i++)
        buf[i] = ' ';
    buf[LINE_LEN] = '\0';
}

void ui_line_put(char *buf, uint8_t col, const char *s)
{
    for (uint8_t i = 0; s[i] && (col + i) < LINE_LEN; i++)
        buf[col + i] = s[i];
}

void ui_line_put_right(char *buf, const char *s)
{
    uint8_t n = ui_str_len(s);
    if (n <= LINE_LEN)
        ui_line_put(buf, (uint8_t)(LINE_LEN - n), s);
}

void ui_u16_to_str(uint16_t v, char *dst)
{
    char tmp[6];
    uint8_t n = 0, i = 0;

    do {
        tmp[n++] = (char)('0' + (v % 10u));
        v /= 10u;
    } while (v && n < 5);

    while (n)
        dst[i++] = tmp[--n];
    dst[i] = '\0';
}

void ui_hex8_to_str(uint8_t v, char *dst)
{
    static const char hex[] = "0123456789ABCDEF";
    dst[0] = hex[v >> 4];
    dst[1] = hex[v & 0x0F];
    dst[2] = '\0';
}

void ui_temp_to_str(const sensor_reading_t *r, char *dst)
{
    int16_t t10;
    uint16_t a;
    uint8_t i = 0;

    if (!r || !r->valid) {
        dst[0] = 'E'; dst[1] = 'R'; dst[2] = 'R'; dst[3] = '\0';
        return;
    }

    /* Avoid dtostrf / soft-float printf — one decimal via ×10 */
    t10 = r->temp_c_x10;
    if (t10 < 0) {
        dst[i++] = '-';
        t10 = (int16_t)(-t10);
    }
    a = (uint16_t)t10;
    if (a >= 1000u) {
        dst[i++] = (char)('0' + (a / 1000u));
        a = (uint16_t)(a % 1000u);
        dst[i++] = (char)('0' + (a / 100u));
        a = (uint16_t)(a % 100u);
    } else if (a >= 100u) {
        dst[i++] = (char)('0' + (a / 100u));
        a = (uint16_t)(a % 100u);
    }
    dst[i++] = (char)('0' + (a / 10u));
    dst[i++] = '.';
    dst[i++] = (char)('0' + (a % 10u));
    dst[i] = '\0';
}

void ui_mmss_to_str(uint16_t sec, char *dst)
{
    uint16_t m = sec / 60u;
    uint16_t s = sec % 60u;
    if (m > 99u)
        m = 99u;
    dst[0] = (char)('0' + (m / 10u));
    dst[1] = (char)('0' + (m % 10u));
    dst[2] = ':';
    dst[3] = (char)('0' + (s / 10u));
    dst[4] = (char)('0' + (s % 10u));
    dst[5] = '\0';
}

void ui_gain_to_str(int16_t x10, char *dst)
{
    uint8_t neg = 0;
    uint16_t v;

    if (x10 < 0) {
        neg = 1;
        x10 = (int16_t)(-x10);
    }
    v = (uint16_t)x10;
    if (neg) {
        dst[0] = '-';
        dst++;
    }
    if (v >= 100u) {
        dst[0] = (char)('0' + (v / 100u));
        dst[1] = (char)('0' + ((v / 10u) % 10u));
        dst[2] = '.';
        dst[3] = (char)('0' + (v % 10u));
        dst[4] = '\0';
    } else {
        dst[0] = (char)('0' + (v / 10u));
        dst[1] = '.';
        dst[2] = (char)('0' + (v % 10u));
        dst[3] = '\0';
    }
}
