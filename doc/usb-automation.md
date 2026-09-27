# UART / AT / MODO USB — SMI Soldering Hot Plate

Contrato del host. Fases, beeps y EEPROM: [program_flows.md](program_flows.md). Si discrepan, manda ese en el proceso térmico; este archivo manda en lo que sale y entra por UART.

UART **9600 8N1**. Una línea = un comando. Fin `\r` o `\n`. Mayúsculas. Trim de espacios/tabs finales. Máximo **31** caracteres de entrada: si se pasa, la línea se tira.

Boot: `\r\nHP\r\n` una vez.

**Protocolo numérico:** `ERROR:`, `ALARM:` y campos `P`/`A` de `$HP` usan enteros. Los nombres de la tabla son solo documentación (ahorro de Flash).

## Sesión

MANUAL y USB no se mezclan. Entrar a USB exige equipo libre.


| Comando | USB previo | Respuesta |
|---------|------------|-----------|
| `AT` | no | `OK` |
| `AT+DEVICEMODE=1` | no | Entra USB si libre → `$HP` + `OK`. Ocupado → `ERROR:4`. Ya USB → `OK` |
| `AT+DEVICEMODE=0` | no | Sale a MANUAL (STOP de sesión), HOME si vista USB → `$HP` + `OK` |


`AT+DEVICEMODE?` **eliminado** — usar `AT+STATUS?`.

PRESS en vista USB: para todo, HOME, `ERROR:8`. Beep CONFIRM ×2.

Resto de comandos (salvo `AT`, `STATUS?`, `DEVICEMODE=`) exigen USB → si no, `ERROR:3`.

## Códigos ERROR

`ERROR:<n>\r\n`


| n | Nombre | Cuándo |
|--:|--------|--------|
| 1 | INVALID_COMMAND | Nombre desconocido en USB / terminador inválido |
| 2 | INVALID_PARAMETER | Argumento malo/rango; START HEAT sin rampas; START PID_TUNE fuera de rango; PIDAPPLY sin DONE |
| 3 | USB_MODE_REQUIRED | Comando USB en MANUAL (también desconocidos en MANUAL) |
| 4 | DEVICE_BUSY | `DEVICEMODE=1` ocupado; START en `PH_FAULT` |
| 5 | PROGRAM_BUSY | PROGRAM/START con ciclo o autotune activo |
| 6 | SENSOR_INVALID | START sin sensor válido |
| 7 | OVER_TEMPERATURE | Corte safety (`temp_max_c`); sustituye la antigua línea `OT` |
| 8 | ABORTED_BY_DEVICE | PRESS en vista USB |


## Códigos ALARM

Espontáneos con sesión USB: `ALARM:<n>\r\n`


| n | Nombre | Cuándo |
|--:|--------|--------|
| 1 | PH_OK | PREHEAT standalone listo |
| 2 | DONE | HEAT fin de rampas (o STOP que cierra como fin) |


## PROGRAM / ACTION (`$HP`)

`P=<n>` = `program_id_t`:


| n | Programa |
|--:|----------|
| 0 | PREHEAT |
| 1 | HEAT |
| 2 | PID_TUNE |


`A=<n>` = fase (`process_phase_t`) salvo autotune:


| n | Fase |
|--:|------|
| 0 | IDLE |
| 1 | DELAY (WAITING) |
| 2 | PREHEAT |
| 3 | STABILIZE |
| 4 | HOLD |
| 5 | RUN |
| 6 | COOLDOWN |
| 7 | ALARM |
| 8 | DONE |
| 9 | FAULT |
| 10 | TUNING (`ATUNE_RUN`) |


## Catálogo AT


| Comando | USB | Efecto | Persiste | OK |
|---------|-----|--------|----------|-----|
| `AT` | no | Ping | — | `OK` |
| `AT+STATUS?` | no | Emite `$HP` | — | `$HP` + `OK` |
| `AT+DEVICEMODE=0\|1` | no | MANUAL/USB | — | `$HP` + `OK` |
| `AT+PROGRAM=0\|1\|2` | sí | Elige programa + carga EEPROM | — | `OK` |
| `AT+TEMP=<°C>` | sí | Consigna programa activo | bloque prog | `OK` |
| `AT+DELAY=<0..3600>` | sí | Delay HEAT (`0` = inmediato) | `ee_heat` | `OK` |
| `AT+PREHEAT=0\|1` | sí | `preheat_en` | global | `OK` |
| `AT+PHPCT=<50..100 paso 5>` | sí | `%` de Ramp1 en PREHEAT HEAT | global | `OK` |
| `AT+STAB=<1..3600>` | sí | `stabilize_s` | global | `OK` |
| `AT+TMIN=<30..100>` | sí | `temp_min_c` (≤ TMAX) | global | `OK` |
| `AT+TMAX=<40..250>` | sí | `temp_max_c` (≥ TMIN) | global | `OK` |
| `AT+AIR=0\|1` | sí | `cooldown_air_en` | global | `OK` |
| `AT+SND=0\|1` | sí | `buzz_nav_en` | global | `OK` |
| `AT+RAMPS=1` | sí | `ramps_en=1` (`=0` error) | global | `OK` |
| `AT+RAMP=<i>,<°C>,<s>` | sí | Escalón 0..3 | `ee_ramp` | `OK` |
| `AT+KP=\|KI=\|KD=<0..999>` | sí | Ganancias ×10 | global | `OK` |
| `AT+ATUNE=<3..10>,<hyst_x10>` | sí | Ciclos + histéresis autotune | global | `OK` |
| `AT+PIDAPPLY` | sí | Copia `atune_*` → PID si `ATUNE_DONE` | global | `OK` |
| `AT+START` | sí | Arranca programa | — | `OK` / `ERROR:n` |
| `AT+STOP` | sí | Parada | — | **solo `OK`** (sin `$HP`) |


## Lectura — `$HP`

Sin campo `DEVICE` (en sesión USB el host ya sabe el modo).

```
$HP,T=<°C.d|--->,P=<prog>,A=<action>,SET=<°C>,DLY=<s>,RUN=<s>,EL=<s>,
P1=0|1,P2=0|1,F=0|1,DU=<0..100>,FL=0|1,
MN=<Tmin>,MX=<Tmax>,KP=,KI=,KD=,
CF=<flags>,SB=<stabilize_s>,RN=<ramp_n>,RI=<ramp_idx>,
AP=<atune_phase>,AC=<cycles>,AG=<target>,AH=<hyst_x10>,
AK=,AI=,AD=
```


| Campo | Significado |
|-------|-------------|
| `T` | Temperatura ×10 o `---` |
| `P` `A` | PROGRAM / ACTION (tablas arriba) |
| `SET` `DLY` `RUN` `EL` | Consigna, delay, remain, elapsed |
| `P1` `P2` `F` `DU` `FL` | PTC1/2, fan, duty, fault |
| `MN` `MX` | Safety min/max °C |
| `KP` `KI` `KD` | PID activo ×10 |
| `CF` | Bits: 0=`preheat_en`, 1=`AIR`, 2=`SND`, 3=`RAMPS`; bits 15..8 = `preheat_pct` |
| `SB` | `stabilize_s` |
| `RN` `RI` | `ramp_n`, `ramp_idx` |
| `AP` | `atune_phase` (0 IDLE, 1 RUN, 2 DONE, 3 FAIL) |
| `AC` `AG` `AH` | ciclos hechos, target, hyst ×10 |
| `AK` `AI` `AD` | Resultado autotune ×10 (RAM; tras DONE) |


No se exponen dirty flags ni se permite forzar calentadores fuera del runner/PID.

## Arranque

```
AT+DEVICEMODE=1
AT+PROGRAM=1
…
AT+START
```

### HEAT (`P=1`)

```
AT+PROGRAM=1
AT+RAMP=0,<°C>,<s>
AT+DELAY=0
AT+PREHEAT=1
AT+PHPCT=80
AT+START
```

### PREHEAT (`P=0`)

```
AT+PROGRAM=0
AT+TEMP=150
AT+START
```

→ `A=2`…`A=3` → `ALARM:1` → hold → `A=8`.

### PID_TUNE (`P=2`)

```
AT+PROGRAM=2
AT+TEMP=150
AT+ATUNE=5,15
AT+START
```

- Consigna debe estar en `[TMIN .. TMAX-10]`; si no → `ERROR:2` (no hay `OK` vacío).
- Stream `$HP` a 1 Hz con `A=10` mientras `AP=1`.
- Al terminar: `AP=2`, `AK/AI/AD` con ganancias.
- Aplicar a PID de trabajo: `AT+PIDAPPLY` → EEPROM. Si no DONE → `ERROR:2`.

Kp/Ki/Kd también se editan con `AT+KP=` / `KI=` / `KD=` (UI Settings ya no edita PID ni lanza Auto).

## Parada

`AT+STOP` → **solo `OK`**. Efectos internos iguales (fin HEAT / abort / cancel atune); el host pide `STATUS?` si necesita foto.

PRESS local → `ERROR:8` (no es STOP).

## Gaps (fase 2)

Sin comando AT aún: `alarm_duration_s`, `alarm_period_s`, lectura de escalones (`AT+RAMP?`).

## Streams

| Stream | Cuándo | Fin |
|--------|--------|-----|
| Foto | `STATUS?`, DEVICEMODE, cambios de fase, beep alarma | un disparo |
| Autotune 1 Hz | START PID_TUNE OK | STOP / fin DONE\|FAIL / fault |


## Nota Flash — autotune solo AT

La página Settings **PID / Auto** se eliminó del binario: autotune y ganancias solo por AT. Medición en esta entrega (mismo árbol, LTO):

| Configuración UI | Program (aprox.) |
|------------------|-----------------:|
| Con página PID + Auto (intermedio del PR) | ~16820 B |
| Sin página PID (actual) | **16098 B** |
| **Δ al quitar UI PID/Auto** | **≈ −720 B** |

El core `pid_atune.c` sigue enlazado (necesario para AT). El ahorro es shell UI + strings i18n asociados, no el algoritmo de autotune.
