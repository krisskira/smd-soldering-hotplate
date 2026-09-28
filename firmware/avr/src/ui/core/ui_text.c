#include "ui_text.h"
#include "ui_digits.h"

uint8_t ui_u16_digits(uint16_t v, char *dst)
{
    char tmp[5];
    uint8_t n = 0, i = 0;

    if (v >= 10000u)
        v = 9999u;
    do {
        tmp[n++] = (char)('0' + (v % 10u));
        v /= 10u;
    } while (v && n < 5u);
    while (n)
        dst[i++] = tmp[--n];
    return i;
}

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

void ui_u16_to_str(uint16_t v, char *dst)
{
    uint8_t n = ui_u16_digits(v, dst);
    dst[n] = '\0';
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
