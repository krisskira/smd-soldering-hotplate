# Features útiles, fuera del binario

Código que ya probamos y que no entra a `make`. La documentación sigue en
`firmware/avr/doc/`. Para volver a usarlo, hay que añadir el `.c` al Makefile.

## Animaciones ST7920

`st7920_animation.c` reproduce un GIF convertido a frame 0 + diffs
(`st7920_animation_run` / `run_all`). El super-loop de producto no lo llama.
Con `-ffunction-sections` el enlazador ya lo descartaba; sacarlo del driver
evita que una vista nueva lo arrastre sin querer.

El icono USB sigue en el binario (`st7920_write_frame_pgm`).

La vista de gráfico de `pid_atune` puede reutilizar este reproductor. Hasta
entonces no se enlaza: los frames de un chart en tiempo real ocuparían flash
y un buffer en RAM por animación activa.

Generador: `tools/gif_to_st7920_anim.py`. Guía: `doc/st7920_pantalla.md`.
