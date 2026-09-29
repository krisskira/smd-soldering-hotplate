/*
 * ST7920 — el path de lista de comandos (line/rect/bitmap/render) se eliminó:
 * la UI usa solo st7920_draw_band / GDRAM directo (st7920_text.c).
 */
#include "st7920.h"
#include "st7920_private.h"

void st7920_clear_commands(void)
{
}
