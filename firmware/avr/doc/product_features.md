# Características del producto — SMI Soldering Hot Plate

Este documento describe **qué hace HotPlate y cómo se comporta**, desde el punto de vista del producto: qué programas tiene, cómo avanza un ciclo de soldadura, qué muestra HotPanel, qué se puede configurar y dónde se guarda.

Firmware en `firmware/avr/`, microcontrolador ATmega16 a 8 MHz. Última actualización: 2026-09-29.

**Documentos relacionados**

| Documento | Cuándo consultarlo |
|-----------|--------------------|
| [program_flows.md](program_flows.md) | Fases, alarmas y EEPROM. **Si hay contradicción térmica con este documento, manda ese.** |
| [architecture.md](architecture.md) | Capas, módulos y super-loop |
| [usb-automation.md](usb-automation.md) | Comandos AT y tramas `$HP` / `$CF` / `$R` |
| [pid_control.md](pid_control.md) | Lazo PI predictivo y autoajuste |
| [ui_style_guide.md](ui_style_guide.md) | Layout, tipografía e iconos de HotPanel |
| [feature_budget.md](feature_budget.md) | Flash por feature y qué se puede recortar |
| [temporizacion_no_bloqueante.md](temporizacion_no_bloqueante.md) | Reloj `avr_delay` sin bloquear |
| [st7920_pantalla.md](st7920_pantalla.md) | Bitmaps, diffs y animaciones LCD |
| [atmega16_pin_definition_hotplate.md](atmega16_pin_definition_hotplate.md) | Pines MCU (vs `config/board_pins.h`) |
| [mejoras_futuras.md](mejoras_futuras.md) | Erratas térmicas y algoritmo pendiente. **No es el comportamiento actual.** |

Si este archivo discrepa del **código**, manda el código y hay que corregir el documento.

---

## 1. Visión general

**HotPlate** ejecuta un **Soldering Profile**: sube la temperatura de forma controlada, la mantiene en cada escalón el tiempo indicado y, al terminar, apaga el calefactor y avisa. Se puede operar de dos maneras, **nunca a la vez**:

- **Modo manual**: desde **HotPanel**, la interfaz a bordo de HotPlate.
- **Modo USB**: desde un PC mediante comandos AT por UART (normalmente con *HotPlate Studio*, en `host-ui/`). Mientras este modo está activo, HotPanel queda bloqueado.

### Hardware implicado

| Función | Componente | Comentario |
|---------|------------|------------|
| Medición de temperatura | PT100 + MAX31865 | Lectura cada 1 s |
| Calefacción | Dos resistencias PTC (PTC1 + PTC2) accionadas por MOC3021 + BT136 | Relé de estado sólido (SSR); no hay relé mecánico |
| Enfriamiento | Bomba de aire / ventilador | Solo al final del ciclo o durante el autotune |
| Avisos | Buzzer piezoeléctrico | Pitidos de proceso |
| Pantalla ST7920 128×64 | Display de **HotPanel** | Interfaz a bordo |

---

## 2. Programas

El firmware tiene **dos programas ejecutables** y el **Soldering Profile** (datos de escalones):

| Programa | Qué hace | Se lanza desde |
|----------|----------|----------------|
| **HEAT** | Ciclo completo de soldadura según el Soldering Profile | HotPanel (casilla Heat) o USB (`AT+RUN=1`) |
| **PID_TUNE** | Autoajuste de las ganancias del control | Solo USB (`AT+RUN=2`) |
| **RAMPS** | *No es un programa*: es el Soldering Profile (hasta 4 escalones) que HEAT recorre. Se guarda en EEPROM y se edita con `AT+CFG=R` o desde Ajustes | — |

> La rampa 1 es el primer escalón del perfil. No hay una fase previa al porcentaje de esa rampa.

### 2.1 HEAT — ciclo de soldadura

Un ciclo HEAT recorre estas fases en orden:

| # | Fase | Qué ocurre | Calefactor | Ventilador | Cuándo avanza |
|---|------|------------|------------|------------|---------------|
| 1 | **Espera** (`WAIT`) | Cuenta atrás antes de empezar. Se omite si el retraso es `00:00` | OFF | OFF | Al llegar a 0 |
| 2 | **Rampa i – subida** (`RUN`) | Sube hacia la temperatura del escalón i (la rampa 1 es el primer escalón). El tiempo **todavía no corre** | PI | OFF | Al entrar en ±`BN` °C del objetivo |
| 3 | **Rampa i – meseta** (`HOLD`) | Mantiene la temperatura del escalón durante su `hold_s` | PI | OFF | Al agotarse `hold_s`: siguiente rampa o fin |
| 4 | **Fin** (`ALM`) | Calefactor apagado, pitidos de aviso y `ALARM:2` por USB | OFF | ON si `cooldown_air_en` | Tras 60 s o al confirmar el usuario |
| 5 | **Enfriamiento** (`AIR`) | Solo si el aire asistido está activado. Sopla hasta bajar a `temp_min_c` | OFF | ON | `T ≤ temp_min_c` |
| 6 | **Terminado** (`END`) | Todo apagado | OFF | OFF | — |

**Detalles importantes del comportamiento**

- **Entrar en meseta.** La subida pasa a meseta al estar a ±`BN` (4 °C por defecto) del objetivo. La meseta no se aborta si la temperatura se sale; corre su `hold_s`.
- **Perfiles.** RSS, rampa a pico, reflow o soldadura son el mismo HEAT con distinto Soldering Profile: la rampa 1 es el primer soak y las siguientes, si las hay, suben o se mantienen.
- **Rampas solo ascendentes.** Se admiten hasta 4 escalones y cada uno debe tener una temperatura igual o mayor que el anterior. Un Soldering Profile descendente se rechaza con `ERROR:2`.
- **El aire solo actúa al final.** El ventilador nunca se enciende entre rampas; solo en la fase de enfriamiento, y solo si `cooldown_air_en` está activado.

**Cancelar un ciclo**

| Cómo se cancela | Resultado |
|-----------------|-----------|
| Desde HotPanel (Cancelar) en espera o rampas | Parada inmediata → `IDLE`. No se emite `ALARM:2` |
| Con `AT+STOP` por USB en esas mismas fases | Se trata como un fin de ciclo → fase de fin + `ALARM:2` |
| Confirmación (HotPanel o `AT+STOP`) durante la fase de fin | Cierra la alarma y pasa a enfriamiento o a terminado |

### 2.2 PID_TUNE — autoajuste

Calcula automáticamente las ganancias del control de temperatura. **Solo se lanza por USB**; HotPanel no ofrece esta opción.

- **Lanzamiento:** `AT+RUN=2,temp,ciclos,hyst[,max_s]`. Los parámetros se pueden guardar antes, sin arrancar, con `AT+CFG=T`.
- **Funcionamiento:** el calefactor se enciende y apaga por completo (control todo/nada) alrededor de la temperatura objetivo, con una histéresis de ±1,5 °C por defecto. Durante los tramos con el calefactor apagado se enciende el ventilador para acortar la bajada y limitar el tiempo que los componentes pasan por encima de la consigna.
- **Resultado:** tras el número de ciclos indicado (5 por defecto, rango 3–10), el firmware mide la amplitud y el periodo de la oscilación y calcula Kp y Ki por el método de Ziegler–Nichols (variante PI, Kd = 0).
- **Guardado:** al terminar, Kp y Ki se escriben solos en EEPROM. No hay `AT+CFG=A`.
- **Límite de tiempo:** si el proceso supera `atune_max_s` (2000 s por defecto, rango 120–3600 s), se aborta con fallo.
- **Telemetría:** en USB el equipo envía un `$HP` por segundo. Mientras dura el autoajuste esa misma trama suma el progreso (`AP`, `AC`) y las ganancias (`AK`, `AI`). Ver [usb-automation.md](usb-automation.md).

Detalle matemático: [pid_control.md](pid_control.md).

---

## 3. Control de temperatura

Durante el precalentamiento, la estabilización y las rampas, la potencia del calefactor la decide un **lazo PI predictivo**:

- **Referencia progresiva.** En lugar de pedir la temperatura final de golpe, el control persigue una referencia interna (`t_ref`) que sube a un ritmo limitado hacia la consigna (1,2 °C/s, constante `RISE_C_X10_DEFAULT`). Así la subida es suave y controlada.
- **Anticipación de la inercia.** El error se calcula con la temperatura que *habrá* dentro de unos segundos (temperatura actual + velocidad de subida × 15 s, constante `LOOKAHEAD_S_DEFAULT`). Esto permite cortar potencia antes de llegar a la consigna y evitar el sobrepaso típico de HotPlate por su masa térmica.
- **Sin término derivativo.** Solo se usan Kp y Ki (Kd = 0). Valores por defecto: Kp = 24,6 y Ki = 1,0 (guardados ×10: 246 y 10).
- **Aplicación al SSR.** La salida del PI es un porcentaje que se aplica como tiempo de encendido dentro de una ventana de 1,5 s (control por proporción de tiempo).
- **Anti-windup.** Si la salida ya está saturada (0 % o 100 %) en la dirección del error, el integrador deja de acumular.
- **Cambio de escalón.** Al pasar a una nueva rampa, la referencia se alinea con la temperatura actual para que la subida arranque limpia, sin arrastrar el estado del tramo anterior.

Las constantes de subida y anticipación están fijadas en compilación (`app_config.h`) y no se guardan en EEPROM, para ahorrar flash.

---

## 4. Seguridad

- **Salidas apagadas por defecto.** Al arrancar el equipo, ante un fallo del sensor o por sobretemperatura, calefactor y ventilador quedan en OFF.
- **Sobretemperatura.** Si una lectura válida alcanza `temp_max_c`, se cortan ambas resistencias, la fase pasa a `FAULT` y por USB se emite `ERROR:7`. No hay pitido en este caso.
- **Límites configurables.**

| Parámetro | Función | Rango | Por defecto |
|-----------|---------|-------|-------------|
| `temp_min_c` | Temperatura mínima de cualquier consigna, y temperatura a la que se detiene el aire de enfriamiento | 50–100 °C | 50 °C |
| `temp_max_c` | Temperatura máxima permitida; por encima se corta la calefacción | 40–250 °C | 250 °C |

Se ajustan por USB con `AT+CFG=S`.

---

## 5. HotPanel (interfaz a bordo)

**HotPanel** es la interfaz de HotPlate: una única vista **Home** con dos casillas laterales — **Heat** y **Settings**. No existen pantallas separadas para USB ni para ajustes; ambos se muestran dentro de Home.

### Casilla Heat

- Temperatura actual centrada a 2× (p. ej. `123.4°C`). Si el sensor no es válido, `ERR`.
- Fase actual.
- Rampa, consigna con `°C` y tiempo de esa etapa (`R2 180°C 01:30`). En reposo y en la espera ese tiempo es el reloj `hh:mm` (tope 12:00). En la meseta es `mm:ss`.
- Línea centrada con el tiempo desde el arranque, en `mm:ss` (`00:00` en reposo). Pasados 99 min se ve `100:00`.
- En el pie, **`RUN`** para arrancar el ciclo o **`STOP`** para cancelarlo.

### Modo USB

Cuando el PC toma el control (`AT+MODE=1`), la casilla Heat muestra la temperatura con la etiqueta **`USB`** a 2× y el pie cambia a **`EXIT`**, que permite recuperar el control manual. No se muestran la fase, el perfil ni el transcurrido.

### Casilla Settings

- Cabecera **`SETUP`** en vídeo inverso, con 2 px de aire debajo. El resaltado de cada opción deja 1 px por encima y por debajo de la letra, y 1 px sin invertir la separa de la siguiente. Se ven cuatro opciones; en DLY la lista sube una fila.
- Lista con las cuatro rampas (**R1…R4**) y el retraso (**`DLY`**): nombre a la izquierda, valor a la derecha. La meseta se muestra en segundos; el retraso, en `hh:mm`.
- Girar hasta la casilla ya enseña la lista. Pulsar entra a editarla; **`EXIT`** vuelve a Heat.

| Fila | Qué se ajusta |
|------|---------------|
| R1…R4 | Temperatura (pasos de 5 °C, entre `temp_min_c` y `temp_max_c`) y meseta (pasos de 30 s, de 30 s a 60 min). R2…R4 se apagan bajando de `temp_min_c` y confirmando con otra pulsación; R1 no se puede apagar |
| `DLY` | Retraso antes de empezar el ciclo, en `hh:mm`, desde `00:00` (inmediato) hasta `12:00`. Pulsar alterna horas y minutos |

### Etiquetas en HotPanel

Todas en inglés y mayúsculas, a través del sistema de traducción (i18n):

| Etiqueta | Significado |
|----------|-------------|
| `IDLE` / `WAIT` | Reposo / cuenta atrás |
| `PRE` / `STAB` | Precalentamiento / estabilización |
| `RUN` | Subida o meseta; también el botón de arranque |
| `ALM` / `AIR` | Aviso de fin / enfriamiento |
| `END` / `ERR` | Terminado / fallo (sensor o sobretemperatura) |
| `STOP` / `EXIT` | Cancelar / salir |
| `OFF` | Rampa apagada, o perfil vacío |
| `DLY` / `USB` / `SETUP` | Fila de retraso, modo USB y cabecera de ajustes |

La lista completa, con el comportamiento de cada modo, está en [ui_style_guide.md](ui_style_guide.md).

---

## 6. Dónde se configura cada cosa

**HotPanel** solo expone lo necesario para el uso diario. El resto se configura por USB (comandos AT o HotPlate Studio).

| Ajuste | HotPanel | USB / HotPlate Studio |
|--------|:--------:|:---------------------:|
| Rampas R1…R4 (temperatura y meseta) | ✔ | ✔ |
| Retraso de inicio (`delay_h` + `delay_m`) | ✔ | ✔ |
| Límites `temp_min_c` / `temp_max_c` | — | ✔ |
| Precalentamiento: activado, %, tiempo de estabilización, bandas | — | ✔ |
| Aire en el enfriamiento (`cooldown_air_en`) | — | ✔ |
| Ganancias PI | — | ✔ |
| Autotune (lanzar y parámetros) | — | ✔ |

> El zumbador solo pita en dos casos: la alarma de proceso (fin de ciclo, arranque rechazado) y un pulso corto cuando HotPanel guarda un valor en EEPROM. No hay pitido al mover el cursor, arrancar, parar ni salir de USB. Ver [feature_budget.md](feature_budget.md).

---

## 7. Avisos y alarmas

| Evento | Por USB | Pitido | Estado en `$HP` (`A=`) |
|--------|---------|--------|------------------------|
| Fin del ciclo HEAT | `ALARM:2` | 3 pulsos (50 ms ON / 80 ms OFF), repetidos cada 5 s mientras dura el aviso | `ALARM` |
| Sobretemperatura | `ERROR:7` | Ninguno | `FAULT` |
| Llegada a una meseta o fin | — | 3 pulsos cortos | Fase nueva |
| Cambio de fase | No hay línea propia | Según la fase | Nombre de la fase nueva |

El estado del proceso se informa siempre dentro de la trama `$HP`, en el campo `A=`; no se envían líneas de alarma adicionales salvo `ALARM:n` y `ERROR:n`. Lista completa y reglas de pitidos: [program_flows.md](program_flows.md).

---

## 8. Datos guardados en EEPROM

La configuración se guarda en EEPROM (versión de formato **v8**). Si al arrancar la versión guardada no coincide con la del firmware, se cargan los valores por defecto (no hay migración).

| Dato | Por defecto | Notas |
|------|-------------|-------|
| Ganancias Kp / Ki (×10) | 246 / 10 | Tras autotune (`AT+CFG=A`) o `AT+CFG=P` |
| `temp_min_c` / `temp_max_c` | 50 / 250 °C | Límites de seguridad |
| `preheat_en` / `preheat_pct` | activado / 80 % | Rango del % : 50–100, pasos de 5 |
| `preheat_band_c` / `preheat_band_exit_c` | ±4 / ±6 °C | Bandas de entrada y salida de la estabilización |
| `atune_cycles_target` | 5 | Ciclos del autotune |
| `atune_hyst_c_x10` | 15 (±1,5 °C) | Histéresis del autotune |
| `atune_max_s` | 2000 s | Tiempo máximo del autotune |
| `stabilize_s` | 30 s | Duración de la estabilización |
| `cooldown_air_en` | activado | Aire en el enfriamiento final |
| Duración / periodo del aviso de fin | 60 s / 5 s | Tiempo total del aviso y cada cuánto se repite el pitido |
| `ee_heat` | — | Retraso de inicio de HEAT |
| `ee_tune` | — | Temperatura objetivo del autotune |
| `ee_ramp` | — | Soldering Profile: hasta 4 rampas (temperatura + meseta) |

No se guardan en EEPROM (son constantes de compilación en `app_config.h`): la velocidad de subida de la referencia (`RISE_C_X10_DEFAULT`) y el horizonte de anticipación (`LOOKAHEAD_S_DEFAULT`).

---

## 9. Núcleo y capa de presentación

El firmware separa dos niveles:

- **Núcleo (core):** HEAT, precalentamiento, control PI y autotune, Soldering Profile, estado central, alarmas y protocolo AT. Es la lógica que decide qué hace HotPlate.
- **Presentación (shell):** la vista Home, el aviso USB, el dibujo en LCD y los textos. Solo muestra el estado y recoge órdenes; **nunca cambia la secuencia del ciclo**.

Esta separación permite modificar la interfaz sin riesgo para el comportamiento térmico. Cuando falta flash, el núcleo y la interfaz aprobada tienen prioridad sobre funciones AT opcionales ([feature_budget.md](feature_budget.md)).

---

## 10. Compilación

La flash del ATmega16 es de **16 384 bytes**, así que el tamaño debe medirse en cada cambio:

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```

Tras tocar tamaño/UI: skill **hotplate-feature-budget** y actualizar [feature_budget.md](feature_budget.md).

---

## 11. Mapa de código (dónde está cada cosa)

### Aplicación

```
src/main.c                      super-loop; g_state
src/app/app_config.h            constantes, HOME_DIRTY_*, EEPROM v8
src/app/app_state.h             app_state_t, fases, PROG_HEAT / PROG_PID_TUNE
src/ui/ui_router.c              → home_view
src/ui/home_view.c              Heat + Settings embebido + overlay USB
src/ui/core/ui_components.c     footer 5×7
src/ui/core/ui_text.c           helpers temp / mm:ss / hh:mm
src/services/program/           program_runner — fases HEAT (con PREHEAT)
src/services/pid.c / pid_atune.c
src/services/cfg_store.c        EEPROM global + heat + rampas
src/services/safety.c           corte → ERROR:7 (temp_max_c)
src/services/device_session.c   MANUAL / USB
src/services/at_cmd.c / telemetry.c
```

`ui_display.c` / `ui_window.c`: presentes en el árbol, **no** enlazados en el Makefile.

### Drivers (`lib/`)

| Módulo | Rol |
|--------|-----|
| `avr_delay` | Timer0 → `delay_ms` / `_sec` / `_min` |
| `avr_spi` / `avr_soft_spi` | ST7920 / MAX31865 |
| `st7920` | LCD 128×64, bandas GDRAM |
| `max31865` | PT100 |
| `encoder` | Polling (CW = cursor baja) |
| `ports` | PTC, fan, buzzer |
| `avr_uart` | 19200 8N1 (igual en HotPlate Studio). TX bloqueante; anillo RX 32 B |
| `fonts` | 5×7 (+ X2 / ICONS 16×16 según enlace; ver budget) |
| `i18n` | PROGMEM CAPS inglés abreviado |

### Hechos cerrados

| Tema | Valor |
|------|-------|
| PTC1 / PTC2 | `board_pins.h`: PD7 / PD6 |
| Encoder | CW = cursor baja |
| Reloj | `F_CPU` **8 MHz** |
| Programas AT | Solo HEAT (`RUN=1`) y PID_TUNE (`RUN=2`); PREHEAT es fase |
| RAMPS | Bloque EEPROM; no lanzable |
| Flash | 16384 B; medir con `make size` |

### Límites conocidos

- Sin vista aparte de alarma (`PH_ALARM` se muestra en Home / overlay USB).
- HotPanel Settings: header `SETUP`, 2 px de aire, R1…R4 + reloj DLY `00:00`…`12:00` (bandas de 9 px + 1 px de separación, 4 visibles con desplazamiento). Heat añade el transcurrido `mm:ss`. PID / aire / autotune solo AT / Studio.
- Sesión USB: un `$HP` a 1 Hz (reposo, HEAT y autotune enriquecido); picos en `pid_atune` (no en `app_state`); sin `$HP,PLOT`.
- Sin guía eléctrica aparte del KiCad + datasheets en `hardware/`.

### Skills / agentes

Ver [AGENTS.md](../../../AGENTS.md) en la raíz del monorepo.
