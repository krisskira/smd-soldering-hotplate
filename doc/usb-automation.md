# UART / AT / MODO USB — SMI Soldering Hot Plate

Contrato del host. Fases, beeps y EEPROM: [program_flows.md](program_flows.md). Si discrepan, manda ese en el proceso térmico; este archivo manda en lo que sale y entra por UART.

UART **9600 8N1**. Una línea = un comando. Fin `\r` o `\n`. Mayúsculas. Trim de espacios/tabs finales. Máximo **31** caracteres de entrada: si se pasa, la línea se tira.

Boot: `\r\nHP\r\n` una vez.

**Protocolo numérico:** `ERROR:`, `ALARM:` y campos `P`/`A` de `$HP` usan enteros. Los nombres de la tabla son solo documentación (ahorro de Flash).

Cinco verbos: `MODE`, `RUN`, `STOP`, `CFG`, `STAT`. PREHEAT no es un programa AT: es la fase de HEAT cuando `preheat_en` está activo.

## Sesión

MANUAL y USB no se mezclan. Entrar a USB exige equipo libre.

| Comando | USB previo | Respuesta |
|---------|------------|-----------|
| `AT` | no | `OK` |
| `AT+MODE=1` | no | Entra USB si libre → `$HP` + `OK`. Ocupado → `ERROR:4`. Ya USB → `OK` |
| `AT+MODE=0` | no | Sale a MANUAL (STOP de sesión), quita overlay USB en Heat → `$HP` + `OK` |

`AT+STAT?` no exige USB. El resto (`CFG`, `CFG?`, `RUN`, `STOP`) sí → si no, `ERROR:3`.

`AT+MODE=1`: overlay en casilla Heat (temp + `USB MODE` + Salir). PRESS Salir: MANUAL, `ERROR:8`, beep CONFIRM ×2.

## Códigos ERROR

`ERROR:<n>\r\n`

| n | Nombre | Cuándo |
|--:|--------|--------|
| 1 | INVALID_COMMAND | Nombre desconocido en USB / terminador inválido |
| 2 | INVALID_PARAMETER | Argumento malo/rango; `RUN=1` sin rampas; `RUN=2` fuera de rango; `CFG=A` sin DONE |
| 3 | USB_MODE_REQUIRED | Comando USB en MANUAL (también desconocidos en MANUAL) |
| 4 | DEVICE_BUSY | `MODE=1` ocupado; `RUN` en `PH_FAULT` |
| 5 | PROGRAM_BUSY | `RUN` con ciclo o autotune activo |
| 6 | SENSOR_INVALID | `RUN` sin sensor válido |
| 7 | OVER_TEMPERATURE | Corte safety (`temp_max_c`) |
| 8 | ABORTED_BY_DEVICE | PRESS Salir en overlay USB |

## Códigos ALARM

Espontáneos con sesión USB: `ALARM:<n>\r\n`

| n | Nombre | Cuándo |
|--:|--------|--------|
| 2 | DONE | HEAT fin de rampas (o `AT+STOP` en marcha, que cierra como fin). Cancel UI → IDLE sin ALARM |

No hay `ALARM:1`. El precalentado de HEAT no emite alarma: al estabilizar pasa a la rampa.

## PROGRAM / ACTION (`$HP`)

`P=<n>` = `program_id_t`:

| n | Programa |
|--:|----------|
| 1 | HEAT |
| 2 | PID_TUNE |

`P=0` no existe.

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
| `AT+STAT?` | no | Emite `$HP` de proceso | — | `$HP` + `OK` |
| `AT+MODE=0\|1` | no | MANUAL/USB | — | `$HP` + `OK` |
| `AT+RUN=1` | sí | Arranca HEAT | — | `OK` / `ERROR:n` |
| `AT+RUN=2,<°C>,<ciclos>,<hyst>[,<max_s>]` | sí | Arranca PID_TUNE y abre stream | global + `ee_tune` | `OK` / `ERROR:n` |
| `AT+STOP` | sí | Parada | — | **solo `OK`** (sin `$HP`) |
| `AT+CFG=S,<min>,<max>` | sí | `temp_min_c`, `temp_max_c` | global | `OK` |
| `AT+CFG=H,<en>,<pct>,<stab>,<delay>,<air>,<snd>` | sí | Flujo HEAT | global + `ee_heat` | `OK` |
| `AT+CFG=P,<kp>,<ki>,<kd>` | sí | Ganancias ×10, 0..999 | global | `OK` |
| `AT+CFG=T,<ciclos>,<hyst>,<max_s>` | sí | Params autotune (sin arrancar) | global | `OK` |
| `AT+CFG=R,<i>,<°C>,<s>` | sí | Escalón 0..3 | `ee_ramp` | `OK` |
| `AT+CFG=R?` | sí | Emite `$R` (escalones) | — | `$R` + `OK` |
| `AT+CFG=A` | sí | Copia resultado autotune → PID si `ATUNE_DONE` | global | `OK` |
| `AT+CFG?` | sí | Emite `$CF` | — | `$CF` + `OK` |

`CFG=H`: `en`/`air`/`snd` son 0 o 1; `pct` 50..100 paso 5; `stab` 1..3600; `delay` 0..3600 (`0` = HEAT inmediato).

`CFG=S`: min 30..100, max 40..250, min ≤ max.

`CFG=R`: °C dentro de min..max, hold 1..3600. Escribir un escalón define el perfil (`ramp_n` crece hasta cubrir el índice). `CFG=R?` lee los cuatro huecos (`$R`); no achica `N`.

`RUN=2`: consigna en `[TMIN .. TMAX-10]`, ciclos 3..10, histéresis ×10 de 1..99; `max_s` opcional 120..3600 (timeout global del autotune; default EEPROM `AMS`, 600 s). Si se omite, usa el valor guardado.

`CFG=T`: ciclos 3..10, hyst 1..99, `max_s` 120..3600. No arranca el proceso.

## Lectura — proceso `$HP`

Sin campo `DEVICE`. Settings no van en esta trama.

```
$HP,T=<°C.d|--->,P=<prog>,A=<action>,SET=<°C>,DLY=<s>,RUN=<s>,EL=<s>,
DU=<0..100>,F=0|1,RI=<ramp_idx>,FL=0|1
```

Con stream de autotune se añade:

```
,AP=<fase>,AC=<ciclos hechos>,AK=<kp>,AI=<ki>,AD=<kd>
```

| Campo | Significado |
|-------|-------------|
| `T` | Temperatura ×10 o `---` |
| `P` `A` | PROGRAM / ACTION |
| `SET` `DLY` `RUN` `EL` | Consigna, delay, remain, elapsed |
| `DU` `F` `RI` `FL` | Duty del banco PTC, fan, índice del escalón en curso (`ramp_idx`), fault. `RI` no es el perfil; el contenido de cada escalón va en `$R` |
| `AP` | `atune_phase` (0 IDLE, 1 RUN, 2 DONE, 3 FAIL). Solo en stream |
| `AC` | Ciclos ya cerrados. Solo en stream |
| `AK` `AI` `AD` | Resultado ×10. Cero hasta DONE. Solo en stream |

`AK`/`AI`/`AD` viven en el autotune, no en `app_state`. El host los grafica desde la trama.

## Lectura — settings `$CF`

Solo `AT+CFG?`. No sale a 1 Hz.

```
$CF,MN=<Tmin>,MX=<Tmax>,KP=,KI=,KD=,PH=0|1,PCT=<pct>,SB=<stabilize_s>,
DLY=<s>,AIR=0|1,SND=0|1,RN=<ramp_n>,AMS=<max_s>
```

`RN` es cuántos escalones cuenta el programa (`ramp_n`, 1..4). No trae °C ni hold; eso sale en `$R`.
`AMS` = timeout global del autotune en segundos (`atune_max_s`, 120..3600).

No se exponen dirty flags ni se permite forzar calentadores fuera del runner/PID.

## Lectura — escalones `$R`

Solo `AT+CFG=R?`. Emite siempre los cuatro huecos (0..3); `N` dice cuántos usa HEAT.

```
$R,N=<n>,0=<°C>/<s>,1=<°C>/<s>,2=<°C>/<s>,3=<°C>/<s>
```

Ejemplo: `$R,N=2,0=180/90,1=220/60,2=100/60,3=125/60`.

## Arranque

```
AT+MODE=1
AT+CFG=R,0,<°C>,<s>
AT+CFG=H,1,80,0,0,1,1
AT+RUN=1
```

### HEAT (`P=1`)

```
AT+CFG=R,0,180,90
AT+CFG=R,1,220,60
AT+CFG=H,1,80,30,0,1,1
AT+RUN=1
```

`CFG=H` activa el precalentado al 80 % de la rampa 1, 30 s de banda, delay 0, aire on, sonido on. `PH=0` en un `CFG=H` salta PREHEAT y STABILIZE y entra en Ramp1.

### PID_TUNE (`P=2`)

```
AT+CFG=T,5,15,1200
AT+RUN=2,150,5,15,1200
```

- Fuera de rango → `ERROR:2` (no hay `OK` vacío).
- Stream `$HP` a 1 Hz con `A=10` y `AP,AC,AK,AI,AD` mientras corre.
- En medio-ciclo OFF: fan ON (acelera enfriamiento / reduce tiempo sobre consigna).
- Timeout global: `AMS` / `max_s` (default 600 s); FAIL si se supera.
- Al terminar: una trama con `AP=2` y `AK/AI/AD`.
- Aplicar al PID de trabajo: `AT+CFG=A` → EEPROM. Si no DONE → `ERROR:2`.

Ganancias de trabajo: `AT+CFG=P,kp,ki,kd`. La UI de Ajustes no edita PID ni lanza Auto.

## Parada

`AT+STOP` → **solo `OK`**. Efectos internos iguales (fin HEAT / abort / cancel atune); el host pide `STAT?` si necesita foto.

PRESS local → `ERROR:8` (no es STOP).

## Gaps

Sin comando AT: `alarm_duration_s`, `alarm_period_s`. `ramp_n` solo crece al escribir un índice alto; no hay forma de achicarlo por AT.

## Streams

| Stream | Cuándo | Fin |
|--------|--------|-----|
| Foto de proceso | `STAT?`, `MODE`, cambios de fase, beep de alarma | un disparo |
| Settings | `CFG?` | un disparo |
| Escalones | `CFG=R?` | un disparo |
| Autotune 1 Hz | `RUN=2` OK | STOP / fin DONE\|FAIL / fault |

## Herramienta host

UI de escritorio en la raíz del repo: [`host-ui/`](../../../host-ui/). Habla este contrato por puerto serie (sin simulador).

```bash
pip install -r host-ui/requirements.txt
python host-ui/app.py
```

## Nota Flash

Medición LTO (`make size`), mismo árbol, UI todavía enlazada:

| | Program |
|--|--------:|
| Catálogo AT anterior (22 comandos, `$HP` con settings) | 16098 B |
| Verbos `MODE/RUN/CFG/STAT` + `$HP` de proceso | 15618 B |
| + `CFG=R?` / trama `$R` | **15738 B** |
| **Δ** vs catálogo anterior | **−360 B** |
