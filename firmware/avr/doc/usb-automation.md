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
| Puerto | UART **19200 8N1** (firmware y HotPlate Studio). Un cliente a 9600 no entiende la sesión |
| Forma | Una línea = un comando |
| Fin de línea | `\r` o `\n` |
| Mayúsculas | Sí |
| Espacios finales | Se ignoran |
| Largo máximo | **31** caracteres; si se pasa, la línea se descarta |

Al encender, HotPlate saluda una vez: `\r\nHP\r\n`. Abrir el puerto no reinicia el equipo, así que si ya estaba en marcha ese saludo ya pasó. HotPlate Studio, al conectar, envía `AT` y toma `OK` como «en línea». `HP` sigue valiendo si se enciende con el puerto abierto.

**Números, no nombres largos.** `ERROR:`, `ALARM:` y los campos `P` / `A` de `$HP` van como enteros. Los nombres de las tablas de abajo son solo para humanos (ahorro de Flash en el micro).

Hay **cinco verbos**: `MODE`, `RUN`, `STOP`, `CFG`, `STAT`.  
La rampa 1 es el primer escalón de HEAT: no es un programa AT ni una fase al % de esa rampa.

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

Con `AT+MODE=1`, HotPanel muestra en Heat la temperatura y la etiqueta **`USB`** a 2×, y el pie **`EXIT`**. No pinta la fase, el perfil ni el transcurrido.  
Pulsar **EXIT** en HotPanel: vuelve a Manual, emite `ERROR:8` y un pitido de confirmación ×2.

---

## Errores (`ERROR:n`)

Formato: `ERROR:<n>\r\n`

| n | Nombre (doc) | Cuándo |
|--:|--------------|--------|
| 1 | INVALID_COMMAND | Comando desconocido / mal formado en USB |
| 2 | INVALID_PARAMETER | Argumento fuera de rango; `RUN=1` sin rampas; `RUN=2` inválido; `CFG=A` ya no existe |
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
| 2 | — | Reservado. Ya no se emite (antes: precalentado al % de la rampa 1) |
| 3 | — | Reservado. Ya no se emite (antes: estabilización de ese %) |
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
| `AT+CFG=H,<delay>,<air>` | sí | Retraso (`00:00`…`12:00`, en segundos) y aire de HEAT | global + `ee_heat` | `OK` |
| `AT+CFG=B,<bn>,<bx>` | sí | Bandas ±°C (entrada / salida) | global | `OK` |
| `AT+CFG=P,<kp>,<ki>` | sí | Ganancias PI ×10 (0…999) | global | `OK` |
| `AT+CFG=T,<ciclos>,<hyst>,<max_s>` | sí | Params autoajuste **sin** arrancar | global | `OK` |
| `AT+CFG=R,<i>,<°C>,<s>` | sí | Escalón 0…3 del Soldering Profile | `ee_ramp` | `OK` |
| `AT+CFG=R?` | sí | Lee escalones | — | `$R` + `OK` |
| `AT+CFG?` | sí | Lee ajustes | — | `$CF` + `OK` |

### Detalles de `CFG`

**`CFG=H`** — retraso y aire de HEAT  
`air` = 0 o 1 · `delay` 0…43200 s (`0` = inmediato, tope 12 h). Dos argumentos. El equipo guarda solo horas y minutos (el resto menor de 60 s se descarta). El antiguo `en,pct,stab` (precalentado al % de la rampa 1) ya no existe: la rampa 1 es el primer escalón, a su propia temperatura. Un argumento de más da `ERROR:2`.

**`CFG=P`** — ganancias PI  
`kp` / `ki` ×10 (0…999). Dos argumentos: el lazo no tiene término D, y un tercer valor (antiguo `kd`) da `ERROR:2`.

**`CFG=B`** — histéresis de bandas  
`bn` entrada ±°C (1…15): al entrar en esa banda, la subida de cualquier rampa pasa a meseta. `bx` se guarda (`bn`…20) y ya no aborta la meseta.

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

Foto del proceso. **No** lleva settings. En USB sale sola cada 1 s (stream de sesión). También sale con `STAT?`, `MODE` y cambios de fase, en los dos modos.

```
$HP,T=<°C.d|--->,P=<prog>,A=<action>,SET=<°C>,DLY=<s 0..43200>,RUN=<s>,EL=<s>,
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
| `DLY` | Retraso configurado, en segundos de reloj (`h×3600+m×60`, tope 43200 = 12:00) |
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
$CF,MN=<Tmin>,MX=<Tmax>,KP=,KI=,BN=<band_c>,BX=<band_exit_c>,DLY=<s>,AIR=0|1,AMS=<max_s>
```

| Campo | Significado |
|-------|-------------|
| `MN` `MX` | Límites de temperatura |
| `KP` `KI` | Ganancias PI ×10. El autotune las escribe solo al terminar |
| `BN` `BX` | Banda para entrar en la meseta de una rampa (±°C). `BX` se guarda; la meseta no se aborta |
| `DLY` | Retraso de arranque en segundos de reloj (mismo criterio que `$HP`) |
| `AIR` | Aire al final de HEAT |
| `AMS` | Timeout global del autoajuste (s) |

No existen `KD` ni `SND` (el firmware ya no guarda Kd ni el flag de sonido). `RN` se omite por Flash.  
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
AT+CFG=H,0,1
AT+CFG=B,4,6
AT+RUN=1
```

En ese ejemplo: retraso `00:00`, aire on, y el ciclo entra directo en la rampa 1. Bandas ±4 / ±6 °C.

Una espera de 1 h 30 min se escribe `AT+CFG=H,5400,1` (`1×3600+30×60`). El tope es `AT+CFG=H,43200,1` (`12:00`). El equipo no guarda esos segundos: los convierte a hora y minuto.

### Autoajuste

```
AT+CFG=T,5,15,1200
AT+RUN=2,150,5,15,1200
```

- Fuera de rango → `ERROR:2`.
- El `$HP` de sesión (1 Hz) pasa a `A=10` y suma `AP,AC,AK,AI`. No hay segunda trama. Ver «Stream de sesión».
- En medio-ciclo OFF el fan ayuda a bajar.
- Timeout: `AMS` / `max_s` (default **2000** s) → FAIL si se supera.
- Al terminar: copia Kp/Ki a EEPROM, trama con `AP=2` y `AK`/`AI`. No hay `AT+CFG=A`.

Ganancias a mano: `AT+CFG=P,kp,ki`. HotPanel no edita PID ni lanza Auto.

### Parar

`AT+STOP` → **solo `OK`**. Internamente cierra HEAT / aborta autoajuste. Como USB sigue abierto, la foto llega sola en el segundo siguiente.

Pulsar **EXIT** en HotPanel → `ERROR:8` (no es lo mismo que `STOP`).

---

## Qué no tiene comando AT

- `alarm_duration_s` / `alarm_period_s` (solo en firmware / EEPROM).
- Achicar el Soldering Profile: reescribir el último escalón activo (`AT+CFG=R,<n-1>,°C,s` fija N) o `AT+CFG=R,<i>,0,<hold>` con `i≥1`.

---

## Cuándo salen las tramas

| Trama | Cuándo | Fin |
|-------|--------|-----|
| `$HP` de sesión | Cada 1 s mientras el equipo está en USB (reposo, HEAT o autoajuste) | `AT+MODE=0`, EXIT en HotPanel o reinicio |
| `$HP` (foto) | `STAT?`, `MODE`, cambio de fase, beep de alarma | Un disparo |
| `$CF` | `CFG?` | Un disparo |
| `$R` | `CFG=R?` | Un disparo |

Durante el autoajuste el `$HP` de sesión lleva además `AP,AC,AK,AI`. La trama de DONE o FAIL es la última con esos campos.

## Stream de sesión

Un solo `$HP` a 1 Hz mientras el equipo está en USB. Reposo, HEAT y autoajuste comparten ese emisor. El autoajuste no abre una segunda trama: añade `AP`, `AC`, `AK` y `AI` mientras `ATUNE_RUN`. `$CF` y `$R` siguen bajo demanda.

En el firmware lo arma el tick del sensor en `main.c`: en USB marca la telemetría pendiente y sale una trama por muestra. Un cambio de fase dentro del segundo puede sumar una foto más. Firmware (`avr_uart_init`) y HotPlate Studio (`serial_link.BAUD`) van a 19200; si solo cambia uno, la sesión deja de entenderse.

| Paso | Qué hace el empuje |
|------|--------------------|
| `AT+MODE=1` | Enciende el `$HP` de estado cada 1 s, aunque no haya programa |
| `AT+RUN=1` | La misma trama pasa a contar HEAT (fase, SET, tiempos, duty, `RI`, `FL`) |
| `AT+RUN=2` | La misma trama suma `AP,AC,AK,AI`. Al salir de `ATUNE_RUN` esos campos desaparecen |
| `AT+MODE=0` | Apaga el periódico. En manual solo quedan las fotos de siempre |
| EXIT en HotPanel | `ERROR:8` y vuelta a Manual: el periódico se apaga |
| `AT+STOP` | Sigue siendo solo `OK`. Si USB sigue abierto, la foto siguiente llega en el segundo siguiente |

**Coste medido.** Flash 15676 B frente a 15696 B antes del cambio (−20 B: se reutiliza el formateador y la condición del tick quedó más corta). RAM 283 B y EEPROM 62 B, sin cambios. A 8 MHz, 19200 sale con `UBRR = 25` (19231 reales, error 0,16 %). La transmisión bloquea el bucle unos 34 ms en reposo, 40 ms en HEAT y 49–54 ms en el peor autoajuste (3–5 % del segundo). El muestreo térmico sigue en 1 s y la ventana del PI en 1,5 s. El anillo de recepción es de 32 bytes (31 útiles, ~16 ms a 19200).

**Órdenes del cliente.** HotPlate Studio escribe una línea y espera `OK` o `ERROR` (candado en `serial_link`). Cada orden de producto cabe en el anillo (la más larga, `AT+RUN=2,…`, son 25 bytes). Una orden que llega entera durante el `$HP` no se recorta. Dos escrituras seguidas sin esperar `OK` pueden pasar de 31 bytes: el firmware tira el exceso, descarta la línea y el cliente hace timeout a los 2 s.

La confirmación de guardado y de arranque es `OK` / `ERROR`. EEPROM se escribe antes de ese `OK`. Un `$HP` que llegue mientras el cliente espera no cierra el comando. `AT+STAT?` sigue valiendo como foto. En USB HotPlate Studio pausa su sondeo para no duplicar la trama y lo reanuda al volver a Manual, al recibir `ERROR:8` o al ver el saludo `HP` de un reinicio. El sondeo y un guardado no se cruzan en el cable: comparten el mismo candado.

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
