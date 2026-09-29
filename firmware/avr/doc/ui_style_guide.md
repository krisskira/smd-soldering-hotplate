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
| Una fuente enlazada | `FONT_5X7` (celda de 6 px: 5 de glifo + 1 de separación). En el panel caben unas **15 columnas** |

`FONT_ICONS` (iconos 16×16) y la variante de temperatura a doble tamaño existen en `lib/fonts/`, pero el Makefile **no las enlaza** (`font_icons.c` y `font8x12.c` quedan fuera) por falta de flash. La barra lateral está diseñada para iconos, pero mientras tanto pinta las letras **`H`** y **`S`** en x = 12 como sustituto provisional. Restaurar los iconos es un objetivo de [feature_budget.md](feature_budget.md). `ui_display.c` y `ui_window.c` tampoco forman parte del binario.

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
| Barra lateral | x = 0…31, y = 0…63 (toda la altura) | Dos casillas **iguales** de 32 × 32 px: Heat (y = 0…31) y Settings (y = 32…63). Cada una está pensada para un icono de **16 × 16 px centrado** (x = 8…23; y = 8…23 y 40…55). La casilla con foco se dibuja invertida |
| Panel | x = 32…127, y = 0…53; texto desde x = 36 | Temperatura y fase, o la lista de ajustes |
| Pie | x = 32…127, y = 54…63 (10 px), solo bajo el panel | Acción de la pulsación: `RUN`, `STOP` o `EXIT` |

El panel solo se borra entero al **cambiar de modo** (Heat, ajustes o USB). Dentro de un modo se repinta la banda que cambió (`HOME_DIRTY_SIDE`, `TEMP`, `BODY`, `FOOT`), para que la temperatura no parpadee. Un borrado total (`st7920_clear_gdram`) ocurre solo al entrar en la vista.

---

## 3. Modo Heat

Es el modo de reposo y el de un ciclo en marcha. La casilla `H` tiene el foco.

Tres líneas centradas:

| Línea | y | Qué muestra |
|-------|---|-------------|
| Temperatura | 3 | `123.4°C` con `FONT_5X7`. Si el sensor no es válido, `ERR` |
| Fase | 15 | Nombre corto de la fase (tabla de abajo) |
| Perfil | 27 | `R2 180 01:30`: rampa, consigna en °C y tiempo `mm:ss` |

La línea de perfil depende del momento:

- **En reposo**, con al menos una rampa: `R1`, la temperatura de la rampa 1 y el retraso configurado (`delay_s`).
- **Sin rampas:** `OFF`. Pulsar `RUN` en ese estado no arranca y suena la alarma.
- **Durante precalentamiento, estabilización, subida y meseta:** el número de rampa en curso, la consigna activa (`t_set_c`) y el tiempo que queda (`t_remain_s`).
- **En espera, enfriamiento y aviso de fin:** sigue mostrando `R1` y su temperatura; el tiempo es `t_remain_s`.

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
| Reposo, foco en Heat | Pasa a la casilla Settings | Arranca HEAT. El retraso se redondea a minutos enteros. Pitido de confirmación (2 pulsos); si no hay rampas o el arranque falla, pitido de alarma | `RUN` |
| Ciclo en marcha (espera, precalentamiento, rampas, enfriamiento o aviso) | No hace nada | Cancela el ciclo (`device_session_safe_stop`). Dos pitidos de confirmación | `STOP` |
| Terminado (`END`) o fallo (`ERR`) | No hace nada | Vuelve a reposo (`IDLE`). Un pitido de navegación | `EXIT` |

Mientras hay un ciclo o la sesión USB está activa, el foco queda forzado en Heat: no se puede abrir ajustes.

Cada lectura de sensor (1 Hz) repinta la temperatura. Si hay un ciclo en marcha, también repinta la fase y el tiempo. El pie no se toca en ese refresco.

---

## 4. Modo USB

Cuando el PC toma el control (`DEVICE_USB`, normalmente `AT+MODE=1`), el panel de Heat se sustituye por:

1. La temperatura, igual que en Heat.
2. La etiqueta **`USB`** en la línea de fase. No se muestran la fase ni la línea de perfil.

| Acción | Efecto |
|--------|--------|
| Girar | Ignorado |
| Pulsar | Sale del modo USB y vuelve al control manual (`device_session_leave_manual`), con foco en Heat. Dos pitidos de confirmación |
| Pie | `EXIT`, invertido |

Ajustes no se puede abrir mientras dure la sesión.

---

## 5. Modo Settings

### Vista previa y edición

Girar hasta la casilla `S` **ya muestra** la lista y recarga de EEPROM las rampas y el retraso de HEAT. En esa vista previa ninguna fila está invertida y el pie está vacío: todavía no se edita. Girar sigue cambiando de casilla.

Pulsar entra en la lista (`HOME_PAGE_SETTINGS`):

- El cursor arranca en R1.
- Girar mueve el cursor por **seis** posiciones: R1, R2, R3, R4, retraso y, al final, el pie `EXIT`.
- La fila bajo el cursor se invierte. Cuando el cursor está en el pie, se invierte `EXIT`.
- Mover el cursor pita una vez (navegación). Pulsar también.
- Pulsar sobre `EXIT` cierra la lista, vuelve el foco a Heat y sale del modo de edición.

### Contenido de cada fila

Cabecera **`SETUP`**, invertida, de 11 px de alto. Debajo, cinco filas de 8 px desde y = 11. El nombre va a la izquierda y el valor a la derecha.

| Fila | En pantalla | Valor |
|------|-------------|-------|
| R1…R4 activas | `R1   150    90` | Temperatura en °C y meseta en **segundos** (no `mm:ss`) |
| Rampa apagada | `R2          OFF` | — |
| Retraso | `DLY      01:00` | `delay_s` en `mm:ss` |

Un asterisco (`*`) marca el campo que se está editando: delante de la temperatura, delante de la meseta, o delante del retraso.

### Editar una rampa

Pulsar recorre tres estados: **nada → temperatura → meseta → nada**. Girar solo cambia el valor cuando hay un campo marcado, y cada paso se guarda en EEPROM al momento.

| Campo | Paso | Límites |
|-------|------|---------|
| Temperatura | 5 °C | Entre `temp_min_c` y `temp_max_c` |
| Meseta (`hold_s`) | 30 s | De 30 s a 60 min |
| Retraso (`delay_s`) | 1 min | De 0 a 60 min. Se guarda en el bloque de HEAT |

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
- Texto nuevo pasa por `I18N_*`. Cabe en 8 caracteres y en las ~15 columnas del panel.
- Girar a la derecha baja el cursor.
- Un ciclo en marcha o una sesión USB dejan el foco en Heat y no abren ajustes.
- Medir el flash (`make size`) antes de volver a enlazar iconos o una fuente más grande.
