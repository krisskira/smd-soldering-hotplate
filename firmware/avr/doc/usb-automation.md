# UART / AT — HotPlate Studio ↔ HotPlate

Contrato de lo que entra y sale por el cable USB/serie.  
HotPlate Studio habla este protocolo; el firmware lo implementa en `at_cmd.c` + `telemetry.c`.

| Si hay duda sobre… | Mira |
|--------------------|------|
| Fases, alarmas, EEPROM, pitidos | [program_flows.md](program_flows.md) (**manda** en el proceso térmico) |
| PI / autoajuste | [pid_control.md](pid_control.md) |
| Flash / qué se puede recortar | [feature_budget.md](feature_budget.md) |

---

## Cómo hablar con HotPlate

| Detalle | Valor |
|---------|-------|
| Puerto | UART **9600 8N1** |
| Forma | Una línea = un comando |
| Fin de línea | `\r` o `\n` |
| Mayúsculas | Sí |
| Espacios finales | Se ignoran |
| Largo máximo | **31** caracteres; si se pasa, la línea se descarta |

Al encender, HotPlate saluda una vez: `\r\nHP\r\n`.

**Números, no nombres largos.** `ERROR:`, `ALARM:` y los campos `P` / `A` de `$HP` van como enteros. Los nombres de las tablas de abajo son solo para humanos (ahorro de Flash en el micro).

Hay **cinco verbos**: `MODE`, `RUN`, `STOP`, `CFG`, `STAT`.  
El precalentamiento **no** es un programa AT: es una fase de HEAT cuando `preheat_en` está activo.

---

## Sesión: Manual vs USB

HotPanel (modo manual) y HotPlate Studio (modo USB) **no** mandan a la vez. Para tomar el control por USB el equipo tiene que estar libre.

| Comando | ¿Hace falta estar en USB? | Qué ocurre |
|---------|---------------------------|------------|
| `AT` | No | Ping → `OK` |
| `AT+MODE=1` | No | Entra en USB si está libre → `$HP` + `OK`. Ocupado → `ERROR:4`. Ya en USB → `OK` |
| `AT+MODE=0` | No | Vuelve a Manual (para la sesión), quita el overlay USB de HotPanel → `$HP` + `OK` |

`AT+STAT?` funciona sin estar en USB.  
El resto (`CFG`, `CFG?`, `RUN`, `STOP`) exige USB → si no, `ERROR:3`.

Con `AT+MODE=1`, HotPanel muestra en Heat la etiqueta **`USB`** y el pie **`EXIT`**.  
Pulsar **EXIT** en HotPanel: vuelve a Manual, emite `ERROR:8` y un pitido de confirmación ×2.

---

## Errores (`ERROR:n`)

Formato: `ERROR:<n>\r\n`

| n | Nombre (doc) | Cuándo |
|--:|--------------|--------|
| 1 | INVALID_COMMAND | Comando desconocido / mal formado en USB |
| 2 | INVALID_PARAMETER | Argumento fuera de rango; `RUN=1` sin rampas; `RUN=2` inválido; `CFG=A` sin autoajuste DONE |
| 3 | USB_MODE_REQUIRED | Comando que exige USB estando en Manual |
| 4 | DEVICE_BUSY | `MODE=1` con el equipo ocupado; `RUN` en fallo (`PH_FAULT`) |
| 5 | PROGRAM_BUSY | `RUN` con un ciclo o autoajuste ya en marcha |
| 6 | SENSOR_INVALID | `RUN` sin sensor válido |
| 7 | OVER_TEMPERATURE | Corte de seguridad (`temp_max_c`) |
| 8 | ABORTED_BY_DEVICE | Pulsar **EXIT** en el overlay USB de HotPanel |

---

## Alarmas (`ALARM:n`)

Líneas espontáneas mientras hay sesión USB: `ALARM:<n>\r\n`

| n | Nombre | Cuándo |
|--:|--------|--------|
| 2 | DONE | HEAT terminó las rampas (o `AT+STOP` en marcha, que cierra como fin). Cancelar desde HotPanel → IDLE **sin** `ALARM` |

No existe `ALARM:1`. El precalentamiento no emite alarma: al estabilizar (o al vencer el timeout de sobrepaso) pasa a la rampa.

---

## Programa y fase en `$HP`

`P=<n>` = qué programa corre:

| n | Programa |
|--:|----------|
| 1 | HEAT (Soldering Profile) |
| 2 | PID_TUNE (autoajuste) |

`P=0` no existe.

`A=<n>` = fase del proceso (salvo autoajuste, que fuerza `A=10`):

| n | Fase | En palabras |
|--:|------|-------------|
| 0 | IDLE | En reposo |
| 1 | DELAY | Espera antes de calentar |
| 2 | PREHEAT | Precalentamiento |
| 3 | STABILIZE | Estabilización |
| 4 | HOLD | Meseta del escalón |
| 5 | RUN | Subida hacia el SET |
| 6 | COOLDOWN | Enfriamiento con aire |
| 7 | ALARM | Aviso de fin |
| 8 | DONE | Listo |
| 9 | FAULT | Fallo / sobretemperatura |
| 10 | TUNING | Autoajuste en curso |

---

## Catálogo de comandos

| Comando | USB | Efecto | Se guarda | Respuesta OK |
|---------|-----|--------|-----------|--------------|
| `AT` | no | Ping | — | `OK` |
| `AT+STAT?` | no | Foto del proceso | — | `$HP` + `OK` |
| `AT+MODE=0\|1` | no | Manual / USB | — | `$HP` + `OK` |
| `AT+RUN=1` | sí | Arranca HEAT | — | `OK` / `ERROR:n` |
| `AT+RUN=2,<°C>,<ciclos>,<hyst>[,<max_s>]` | sí | Arranca autoajuste + stream | global + `ee_tune` | `OK` / `ERROR:n` |
| `AT+STOP` | sí | Parada | — | **solo `OK`** (sin `$HP`) |
| `AT+CFG=S,<min>,<max>` | sí | Límites de temperatura | global | `OK` |
| `AT+CFG=H,<en>,<pct>,<stab>,<delay>,<air>,<snd>` | sí | Flujo HEAT | global + `ee_heat` | `OK` |
| `AT+CFG=B,<bn>,<bx>` | sí | Bandas ±°C (entrada / salida) | global | `OK` |
| `AT+CFG=P,<kp>,<ki>,<kd>` | sí | Ganancias ×10 (0…999) | global | `OK` |
| `AT+CFG=T,<ciclos>,<hyst>,<max_s>` | sí | Params autoajuste **sin** arrancar | global | `OK` |
| `AT+CFG=R,<i>,<°C>,<s>` | sí | Escalón 0…3 del Soldering Profile | `ee_ramp` | `OK` |
| `AT+CFG=R?` | sí | Lee escalones | — | `$R` + `OK` |
| `AT+CFG=A` | sí | Copia resultado autoajuste → PID (si DONE) | global | `OK` |
| `AT+CFG?` | sí | Lee ajustes | — | `$CF` + `OK` |

### Detalles de `CFG`

**`CFG=H`** — precalentamiento y arranque de HEAT  
`en` / `air` / `snd` = 0 o 1 · `pct` 50…100 paso 5 · `stab` 1…3600 · `delay` 0…3600 (`0` = inmediato).  
`snd` sigue aceptándose por compatibilidad, pero **el sonido de navegación no es feature de producto** y **no** sale en `$CF`.

**`CFG=B`** — histéresis de bandas  
`bn` entrada ±°C (1…15) · `bx` salida ±°C (`bn`…20). Sirve en precalentamiento y en el approach de cada rampa.

**`CFG=S`** — límites  
min 30…100 · max 40…250 · min ≤ max.

**`CFG=R`** — Soldering Profile  
°C dentro de min…max · hold 1…3600. Escribir el escalón `i` **fija** `ramp_n = i+1` y limpia los huecos altos (así se puede achicar N).  
`temp=0` con `i≥1` deshabilita desde ese índice.  
Al `AT+RUN=1` el perfil debe ser **no decreciente** → si no, `ERROR:2`.  
Lectura: `CFG=R?` → `$R`.

**`CFG=T` / `RUN=2`** — autoajuste  
Consigna en `[Tmin .. Tmax−10]` · ciclos 3…10 · histéresis ×10 de 1…99 · `max_s` opcional 120…3600 (default EEPROM `AMS`, 2000 s).  
`CFG=T` solo guarda; `RUN=2` arranca.

---

## Lectura — proceso `$HP`

Foto del proceso. **No** lleva settings. Sale con `STAT?`, `MODE`, cambios de fase, y a 1 Hz durante el autoajuste.

```
$HP,T=<°C.d|--->,P=<prog>,A=<action>,SET=<°C>,DLY=<s>,RUN=<s>,EL=<s>,
DU=<0..100>,F=0|1,RI=<ramp_idx>,FL=0|1
```

Con stream de autoajuste se añade:

```
,AP=<fase>,AC=<ciclos hechos>,AK=<kp>,AI=<ki>
```

| Campo | Significado |
|-------|-------------|
| `T` | Temperatura (°C con décima) o `---` si el sensor no vale |
| `P` `A` | Programa / fase (tablas de arriba) |
| `SET` | Consigna actual (°C) |
| `DLY` | Retraso configurado (s) |
| `RUN` | Tiempo restante de la fase (s) |
| `EL` | Tiempo transcurrido (s) |
| `DU` | Duty del banco PTC (0…100 %) |
| `F` | Ventilador 0/1 |
| `RI` | Índice del escalón en curso (`ramp_idx`). El contenido del perfil va en `$R` |
| `FL` | Fault 0/1 |
| `AP` | Fase del autoajuste: 0 IDLE, 1 RUN, 2 DONE, 3 FAIL |
| `AC` | Ciclos ya cerrados |
| `AK` `AI` | Kp / Ki resultado ×10 (cero hasta DONE) |

`AK` / `AI` viven en el autoajuste, no en `app_state`. HotPlate Studio los grafica desde la trama.  
**Nota:** `AD` (Kd) **ya no se emite** (siempre 0; ahorro de Flash).

---

## Lectura — ajustes `$CF`

Solo con `AT+CFG?` (no a 1 Hz).

```
$CF,MN=<Tmin>,MX=<Tmax>,KP=,KI=,PH=0|1,PCT=<pct>,SB=<stabilize_s>,
BN=<band_c>,BX=<band_exit_c>,DLY=<s>,AIR=0|1,AMS=<max_s>
```

| Campo | Significado |
|-------|-------------|
| `MN` `MX` | Límites de temperatura |
| `KP` `KI` | Ganancias PI ×10 (`KD` omitido: siempre 0) |
| `PH` `PCT` `SB` | Precalentamiento on/off, %, segundos de estabilización |
| `BN` `BX` | Bandas entrada / salida (±°C) |
| `DLY` | Retraso de arranque (s) |
| `AIR` | Aire al final de HEAT |
| `AMS` | Timeout global del autoajuste (s) |

Omitidos a propósito por Flash: `KD`, `SND`, `RN`.  
La cuenta de escalones (`ramp_n`) se lee en `$R` como `N=`.

No se exponen dirty flags ni se pueden forzar calentadores fuera del runner/PID.

---

## Lectura — Soldering Profile `$R`

Solo con `AT+CFG=R?`. Siempre emite los cuatro huecos (0…3); `N` dice cuántos usa HEAT.

```
$R,N=<n>,0=<°C>/<s>,1=<°C>/<s>,2=<°C>/<s>,3=<°C>/<s>
```

Ejemplo: `$R,N=2,0=180/90,1=220/60,2=100/60,3=125/60`.

---

## Recetas rápidas

### Tomar el control y lanzar HEAT

```
AT+MODE=1
AT+CFG=R,0,180,90
AT+CFG=R,1,220,60
AT+CFG=H,1,80,30,0,1,0
AT+CFG=B,4,6
AT+RUN=1
```

En ese ejemplo: precalentamiento al 80 % de Ramp1, 30 s de meseta, delay 0, aire on, `snd=0`. Bandas ±4 / ±6 °C.  
Con `PH=0` (primer argumento de `H`) se salta precalentamiento y estabilización.

### Autoajuste

```
AT+CFG=T,5,15,1200
AT+RUN=2,150,5,15,1200
```

- Fuera de rango → `ERROR:2`.
- Stream `$HP` a 1 Hz con `A=10` y `AP,AC,AK,AI`.
- En medio-ciclo OFF el fan ayuda a bajar.
- Timeout: `AMS` / `max_s` (default **2000** s) → FAIL si se supera.
- Al terminar: trama con `AP=2` y `AK`/`AI`.
- Aplicar al lazo: `AT+CFG=A` → EEPROM. Si no está DONE → `ERROR:2`.

Ganancias a mano: `AT+CFG=P,kp,ki,kd`. HotPanel no edita PID ni lanza Auto.

### Parar

`AT+STOP` → **solo `OK`**. Internamente cierra HEAT / aborta autoajuste; Studio pide `STAT?` si quiere una foto.

Pulsar **EXIT** en HotPanel → `ERROR:8` (no es lo mismo que `STOP`).

---

## Qué no tiene comando AT

- `alarm_duration_s` / `alarm_period_s` (solo en firmware / EEPROM).
- Achicar el Soldering Profile: reescribir el último escalón activo (`AT+CFG=R,<n-1>,°C,s` fija N) o `AT+CFG=R,<i>,0,<hold>` con `i≥1`.

---

## Cuándo salen las tramas

| Trama | Cuándo | Fin |
|-------|--------|-----|
| `$HP` (foto) | `STAT?`, `MODE`, cambio de fase, beep de alarma | Un disparo |
| `$CF` | `CFG?` | Un disparo |
| `$R` | `CFG=R?` | Un disparo |
| `$HP` autotune 1 Hz | Tras `RUN=2` OK | `STOP` / DONE / FAIL / fault |

---

## HotPlate Studio

App de escritorio en [`host-ui/`](../../../host-ui/). Habla este contrato por puerto serie (sin simulador).

```bash
pip install -r host-ui/requirements.txt
python host-ui/app.py
```

---

## Nota de Flash

ATmega16: **16384 B**. Tras tocar el protocolo: `make size` y actualizar [feature_budget.md](feature_budget.md) (skill `hotplate-feature-budget`).  
UI aprobada (iconos, temp ×2) no se sacrifica para meter campos AT opcionales.
