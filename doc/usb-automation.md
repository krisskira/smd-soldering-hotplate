# UART / AT / MODO USB — SMI Soldering Hot Plate

UART 9600 8N1. Sesión exclusiva MANUAL/USB. Flujos: [program_flows.md](program_flows.md).

Entrada: solo `AT+DEVICEMODE=USB` (equipo libre). PRESS en vista USB → HOME.

## Lanzamiento

| Programa | UI | USB/AT |
|----------|----|--------|
| HEAT | Home (delay + start) | `AT+PROGRAM=HEAT` + `AT+START` |
| PREHEAT | No | Sí |
| PID_TUNE | Ajustes→PID | Sí |
| RAMPS | No | `AT+RAMP` edita |

Tokens **eliminados:** `START_IN`, `STOP_IN`. Usar `HEAT` + `AT+DELAY`.

## Comandos

| Comando | Efecto |
|---------|--------|
| `AT+PROGRAM=HEAT\|PREHEAT\|PID_TUNE` | Selecciona programa |
| `AT+TEMP=<temp_min..temp_max>` | Setpoint del programa activo |
| `AT+DELAY=<0..3600>` | Delay de HEAT (0 = inmediato) |
| `AT+PREHEAT=0\|1` | Flag global EEPROM |
| `AT+RAMPS=1` | Confirma rampas (`=0` error) |
| `AT+RAMP=<i>,<temp>,<sec>` | Escalón; temp en rango safety |
| `AT+START` / `AT+STOP` | Arranca / FIN o abort |

## Secuencia HEAT

```
[DELAY si delay_s>0] → si preheat_en: PREHEAT(preheat_pct% de Ramp1) → estabiliza
  → RUN Ramp1..n a T plena → ALARM:DONE → aire hasta temp_min_c
```

`preheat_en=0` salta el precalentado. PREHEAT standalone sigue yendo a `t_set` pleno: `ALARM:PH-OK`.

Sobretemperatura: línea UART `OT` (over-temperature, `temp ≥ temp_max_c`). No es un pitido.

## `$HP`

`PROGRAM=HEAT|PREHEAT|PID_TUNE`, `ACTION=…`, `RUN=…`.

`PID_TUNE` lanzado por USB activa stream: la misma trama `$HP` sale a 1 Hz (`T`, `SET`, `DUTY` 0 o 100, `P1`/`P2`, `ACTION=TUNING`) y una más al pasar a DONE o FAIL. Cancel no añade trama. Desde la UI no hay stream: Ajustes → PID → Auto muestra `RUN` / `OK` / `FAIL` y deja picos y ganancias en `app_state`.

`preheat_pct` (Ajustes → P%, 50..100, paso 5) no tiene comando AT. `AT+PREHEAT=0|1` solo habilita o salta el tramo.
