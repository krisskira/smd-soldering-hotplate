# Guía de estilo — HotPanel (ST7920 128×64)

Cómo está dibujada y cómo se comporta **HotPanel**, la interfaz a bordo de HotPlate. Describe el binario actual (`home_view.c`). Complementa [product_features.md](product_features.md) (qué hace el producto) y [architecture.md](architecture.md) (cómo está organizado el código). Bitmaps, diffs y animaciones: [st7920_pantalla.md](st7920_pantalla.md).

Actualizado: 2026-09-29.

Hay **una sola vista**, `VIEW_HOME`. El router (`ui_router.c`) siempre entra ahí. Lo que el usuario percibe como pantallas distintas son modos de esa misma vista: Heat en reposo, Heat con un ciclo en marcha, aviso USB, lista de ajustes y el cierre de un ciclo terminado o fallido.

---

## 1. Límites de la pantalla

| Recurso | Qué implica al diseñar |
|---------|------------------------|
| 128 × 64 px | Todo cabe en un rectángulo pequeño; no hay scroll ni segundas páginas |
| 1 bit (encendido / apagado) | Sin grises, degradados ni anti-alias. El único énfasis es **invertir** la banda: fondo encendido y glifo apagado |
| Encoder + pulsación | Girar a la derecha (`EVT_ENCODER_NEXT`) avanza el cursor **hacia abajo**. Girar a la izquierda sube. Pulsar confirma |
| Fuentes enlazadas | `FONT_5X7` (celda de 6 px: 5 de glifo + 1 de separación; en el panel caben unas **15 columnas**), `FONT_5X7_X2` (la misma tabla a 2×, celda de 12 px) y `FONT_ICONS` (16×16) |

`font8x12.c` no se enlaza. `ui_display.c` y `ui_window.c` tampoco forman parte del binario. El icono USB de `font_icons.c` solo se compila con `-DFONT_ICONS_USB`: el overlay USB usa el texto `USB` a 2×.

### Glifos 5×7

Cada glifo son 5 bytes, uno por columna; el bit 0 es la fila superior y el bit 6 la inferior. Una letra simétrica tiene que tener **una fila central (fila 3)** donde se crucen los trazos: con 7 filas hay 3 arriba, 1 en el centro y 3 abajo. Por ejemplo, la `X` es `0x63, 0x14, 0x08, 0x14, 0x63`:

```
X...X   fila 0
X...X   fila 1
.X.X.   fila 2
..X..   fila 3  ← cruce
.X.X.   fila 4
X...X   fila 5
X...X   fila 6
```

La diagonal de 5 columnas no cabe en 7 filas a un píxel por fila, así que los extremos se duplican (filas 0–1 y 5–6). Un patrón de diagonal pura (`0x41, 0x22, 0x14, 0x22, 0x41`) deja la fila 3 vacía y la letra se ve partida, sobre todo a 2×.

El límite de flash es **16 384 bytes**. Cualquier cambio visual se mide con `make size`.

---

## 2. Distribución de la pantalla

```
x=0        x=32                            x=127
┌──────────┬──────────────────────────────────┐ y=0
│          │                                  │
│ ┌──────┐ │                                  │
│ │ Heat │ │                                  │
│ │16×16 │ │             panel                │
│ └──────┘ │                                  │
│          │                                  │
├──────────┤                                  │ y=32
│          │                                  │
│ ┌──────┐ │                                  │
│ │ Set. │ │                                  │
│ │16×16 │ ├──────────────────────────────────┤ y=54
│ └──────┘ │  pie (RUN / STOP / EXIT)         │
│          │                                  │
└──────────┴──────────────────────────────────┘ y=63
```

| Zona | Posición | Contenido |
|------|----------|-----------|
| Barra lateral | x = 0…31, y = 0…63 (toda la altura) | Dos casillas **iguales** de 32 × 32 px: Heat (y = 0…31) y Settings (y = 32…63), cada una con su icono `FONT_ICONS` de **16 × 16 px centrado** (x = 8…23; y = 8…23 y 40…55). La casilla con foco se dibuja invertida. Una línea vertical en x = 31 separa la barra del panel |
| Panel | x = 32…127, y = 0…53; texto desde x = 36 | Temperatura y fase, o la lista de ajustes |
| Pie | x = 32…127, y = 54…63 (10 px), solo bajo el panel | Acción de la pulsación: `RUN`, `STOP` o `EXIT` |

El panel solo se borra entero al **cambiar de modo** (Heat, ajustes o USB). Dentro de un modo se repinta la banda que cambió (`HOME_DIRTY_SIDE`, `TEMP`, `BODY`, `FOOT`), para que la temperatura no parpadee. Un borrado total (`st7920_clear_gdram`) ocurre solo al entrar en la vista.

---

## 3. Modo Heat

Es el modo de reposo y el de un ciclo en marcha. La casilla Heat tiene el foco.

Cuatro líneas centradas. Temperatura, fase y perfil siguen en su sitio; el transcurrido va debajo.

| Línea | y | Qué muestra |
|-------|---|-------------|
| Temperatura | 3 (14 px) | `123.4°C` con `FONT_5X7_X2` (7 × 12 px = 84 px). Si el sensor no es válido, `ERR` |
| Fase | 21 | Nombre corto de la fase (tabla de abajo) |
| Perfil | 33 | `R2 180°C 01:30`: rampa, consigna con `°C` y tiempo. En meseta es `mm:ss`; el retraso es `hh:mm` |
| Transcurrido | 45 | `mm:ss` desde el arranque (`t_elapsed_s`). En reposo, `00:00`. Pasados 99 min el minuto gana un dígito (`100:00`). Termina en y = 52; el pie sigue en y = 54 |

La línea de perfil depende del momento:

- **En reposo**, con al menos una rampa: `R1`, la temperatura de la rampa 1 y el retraso configurado (`hh:mm`, tope 12:00).
- **Sin rampas:** `OFF`. Pulsar `RUN` en ese estado no arranca y suena la alarma.
- **Durante precalentamiento, estabilización, subida y meseta:** el número de rampa en curso, la consigna activa (`t_set_c`) y el tiempo que queda (`t_remain_s`).
- **En espera:** `R1`, la temperatura de la rampa 1 y el tiempo que queda en `hh:mm`.
- **En enfriamiento y aviso de fin:** sigue mostrando `R1` y su temperatura; el tiempo es `t_remain_s` en `mm:ss`.

### Nombres de fase en pantalla

El nombre sale de `program_phase_name()`. La meseta (`PH_HOLD`) comparte la etiqueta de la subida.

| Fase interna | En pantalla |
|--------------|-------------|
| Reposo | `IDLE` |
| Cuenta atrás | `WAIT` |
| Precalentamiento | `PRE` |
| Estabilización | `STAB` |
| Subida y meseta | `RUN` |
| Enfriamiento | `AIR` |
| Aviso de fin | `ALM` |
| Terminado | `END` |
| Fallo | `ERR` |

### Qué hace el mando

| Estado | Girar | Pulsar | Pie |
|--------|-------|--------|-----|
| Reposo, foco en Heat | Pasa a la casilla Settings | Arranca HEAT con el reloj `hh:mm` ya guardado. Si no hay rampas o el arranque falla, pitido de alarma | `RUN` |
| Ciclo en marcha (espera, precalentamiento, rampas, enfriamiento o aviso) | No hace nada | Cancela el ciclo (`device_session_safe_stop`) | `STOP` |
| Terminado (`END`) o fallo (`ERR`) | No hace nada | Vuelve a reposo (`IDLE`) | `EXIT` |

Mientras hay un ciclo o la sesión USB está activa, el foco queda forzado en Heat: no se puede abrir ajustes.

Cada lectura de sensor (1 Hz) repinta la temperatura. Si hay un ciclo en marcha, también repinta la fase, el perfil y el transcurrido. El pie no se toca en ese refresco.

---

## 4. Modo USB

Cuando el PC toma el control (`DEVICE_USB`, normalmente `AT+MODE=1`), el panel de Heat se sustituye por:

1. La temperatura, igual que en Heat.
2. La etiqueta **`USB`** a 2× (`FONT_5X7_X2`) en la línea de fase. No se muestran la fase, el perfil ni el transcurrido.

| Acción | Efecto |
|--------|--------|
| Girar | Ignorado |
| Pulsar | Sale del modo USB y vuelve al control manual (`device_session_leave_manual`), con foco en Heat |
| Pie | `EXIT`, invertido |

Ajustes no se puede abrir mientras dure la sesión.

---

## 5. Modo Settings

### Vista previa y edición

Girar hasta la casilla Settings **ya muestra** la lista y recarga de EEPROM las rampas y el retraso de HEAT. En esa vista previa ninguna fila está invertida y el pie está vacío: todavía no se edita. Girar sigue cambiando de casilla.

Pulsar entra en la lista (`HOME_PAGE_SETTINGS`):

- El cursor arranca en R1.
- Girar mueve el cursor por **seis** posiciones: R1, R2, R3, R4, retraso y, al final, el pie `EXIT`.
- La fila bajo el cursor se invierte. Cuando el cursor está en el pie, se invierte `EXIT`.
- Mover el cursor y entrar o salir de un campo no pitan.
- Pulsar sobre `EXIT` cierra la lista, vuelve el foco a Heat y sale del modo de edición.

### Contenido de cada fila

Cabecera **`SETUP`**, invertida, de 11 px de alto. Dos píxeles en blanco (y = 11…12) y después cinco filas de 7 px desde y = 13, separadas por 1 px que no entra en el inverso. El nombre va a la izquierda y el valor a la derecha. La última fila termina en y = 51; el pie sigue en y = 54.

| Fila | En pantalla | Valor |
|------|-------------|-------|
| R1…R4 activas | `R1   150    90` | Temperatura en °C y meseta en **segundos** (no `mm:ss`) |
| Rampa apagada | `R2          OFF` | — |
| Retraso | `DLY      01:30` | Reloj `hh:mm` (`01:30` = 1 h 30 min). Tope `12:00` |

Un asterisco (`*`) marca el campo que se está editando: delante de la temperatura, delante de la meseta, delante de las horas del retraso (`*01:30`) o en los dos puntos al editar minutos (`01*30`).

### Editar una rampa

Pulsar recorre tres estados: **nada → temperatura → meseta → nada**. Girar solo cambia el valor cuando hay un campo marcado, y cada paso se guarda en EEPROM al momento, con un pulso corto de confirmación.

| Campo | Paso | Límites |
|-------|------|---------|
| Temperatura | 5 °C | Entre `temp_min_c` y `temp_max_c` |
| Meseta (`hold_s`) | 30 s | De 30 s a 60 min |
| Retraso, horas | 1 h | De 0 a 12. En 12 h los minutos pasan a 00. Pulsar entra aquí primero (`*HH:MM`) |
| Retraso, minutos | 1 min | De 0 a 59. Segunda pulsación (`HH*MM`). En 12 h no se mueven |

Reglas al apagar o encender rampas:

- **R1 no se apaga.** Si se intenta bajar de `temp_min_c`, se queda en ese mínimo.
- **R2…R4** se apagan en dos pasos: bajar de `temp_min_c` deja la temperatura en 0 (pendiente de apagar, la fila sigue mostrando el número 0) y la pulsación siguiente confirma, recortando el perfil en esa rampa (`ramp_n`).
- Una rampa en `OFF` se enciende girando a la derecha o pulsando. Nace con temperatura `temp_min_c` y meseta de 30 s, y el cursor queda editando la temperatura.
- Encender R3 enciende también las anteriores que faltaran, porque el perfil es siempre R1…Rn sin huecos.

### Qué no se repinta

Con la lista visible, una lectura nueva del sensor **no** marca la pantalla. Así el cursor y los valores no parpadean cada segundo.

---

## 6. Textos

Todos los textos salen de `lib/i18n/i18n.c` mediante `i18n_tr_hash(I18N_*)`. Son inglés, mayúsculas y como mucho 8 caracteres (`SETTINGS` no cabe: la cabecera es `SETUP`).

| Id | Texto | Dónde |
|----|-------|-------|
| `I18N_PHASE_IDLE` … | `IDLE` `WAIT` `PRE` `STAB` `RUN` `AIR` `ALM` `END` `ERR` | Línea de fase |
| `I18N_BTN_START` | `RUN` | Pie para arrancar |
| `I18N_BTN_CANCEL` | `STOP` | Pie para cancelar |
| `I18N_USB_EXIT` | `EXIT` | Pie de USB, de ajustes y de fin/fallo |
| `I18N_TITLE_USB` | `USB` | Línea central del modo USB |
| `I18N_TITLE_SETTINGS` | `SETUP` | Cabecera de ajustes |
| `I18N_SET_DELAY` | `DLY` | Fila de retraso |
| `I18N_OFF` | `OFF` | Rampa apagada, o perfil vacío en Heat |

No hay glifo de “intro” en el pie: la acción es solo la palabra.

---

## 7. Checklist al tocar HotPanel

- Repintar solo la banda sucia. El panel completo se borra al cambiar de modo, no en cada lectura.
- Heat conserva temp 2×, fase y perfil (`Rx T°C`). El transcurrido va en y = 45 (`00:00` en reposo). El overlay USB no lo pinta.
- Setup: 2 px bajo `SETUP` y 1 px entre opciones, fuera del inverso. La lista termina antes del pie (y = 54).
- Texto nuevo pasa por `I18N_*`. Cabe en 8 caracteres y en las ~15 columnas del panel.
- Girar a la derecha baja el cursor.
- Un ciclo en marcha o una sesión USB dejan el foco en Heat y no abren ajustes.
- Medir el flash (`make size`) antes de volver a enlazar iconos o una fuente más grande.
