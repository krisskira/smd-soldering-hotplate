# Erratas y mejoras futuras

Trabajo **no implementado**. El contrato vigente sigue en [program_flows.md](program_flows.md) y [pid_control.md](pid_control.md). Este archivo no cambia HEAT, el PI ni el autotune.

Fecha: 2026-09-29.  
Aleación de referencia: **Sn63/Pb37** (eutéctico **183 °C**).  
Techo físico declarado de la placa: **190 °C**. En el repositorio no hay ninguna traza que lo mida.

Perfil de horno usado solo como forma de referencia (es de soldadura sin plomo; liquidus ≈ 217 °C, pico 260 °C): imagen de resina y [Reflow soldering profile](https://www.superengineer.net/blog/soldering-reflow-profile#rsp).

---

## 1. Qué dicen las trazas reales

Las capturas y CSV están en `docs/heat-results/` y `docs/atune-results/`. Las de HEAT son del 2026-09-28 y todavía nombran `Precalentado` / `Estabilizando`. El firmware actual ya no tiene esa fase: la rampa 1 es el primer escalón. Sirven para la **planta** (inercia, pendiente, cola, enfriamiento), no para copiar aquella máquina de estados.

No hay muestras por encima de **130 °C**. Todo lo que sigue a partir de ahí es extrapolación y hay que medirlo.

### Subida a plena potencia (autotune, SET 100 °C)

`hotplate_tune_trace-2.csv` y `hotplate_tune_trace_ajustado.csv`, primer tramo con el calentador al 100 %:

| Tramo | Tiempo | Pendiente |
|-------|--------|-----------|
| ~30 → 50 °C | 94–96 s desde el arranque | 0,36–0,39 °C/s |
| 50 → 60 | 20–21 s | 0,47–0,50 °C/s |
| 60 → 70 | 16–18 s | 0,55–0,63 °C/s |
| 70 → 80 | 13–15 s | 0,66–0,77 °C/s |
| 80 → 90 | 14 s | 0,72 °C/s |
| 90 → 100 | 13–14 s | 0,71–0,75 °C/s |
| 30 → 100 | **173–176 s** | media ≈ 0,40 °C/s |

A 100 °C la planta **todavía acelera**. Ese punto no es el techo.

Al cortar el SSR en 101,5 °C la temperatura siguió hasta **117,8 °C (+16,3 °C) en 41 s**, ya con el calentador apagado. Esa cola es de un corte brusco a ~0,7 °C/s. No es el overshoot de un escalón PI de 10 °C.

### HEAT en lazo cerrado, hasta 130 °C

`hotplate_heat_trace-4.csv` es la corrida usable (placa ya a 65 °C, escalones de 10 °C):

| Escalón | Approach hasta la banda | Qué hizo la meseta |
|---------|-------------------------|--------------------|
| 80 °C | 84 s hasta 76 °C | 31 s: 75 → 78 °C, sin pasarse |
| 100 °C | 71 s, 78 → 95 °C, duty medio 66 % | **30 s no aplanan**: 95 → **103,4 °C** (+3,4 °C) con duty ~2 % |
| 110 °C | 51 s, ya venía en 103 °C | 60 s: 105 → 107 °C |
| 120 °C | 60 s, 107 → 115 °C, duty ~48 % | 30 s: 115 → 119,6 °C (no llega al SET) |
| 130 °C | 58 s, 120 → 125 °C, duty ~46 % | 30 s: 125 → **129,3 °C** |

Consecuencias para elegir tiempos:

- Una meseta de **30 s no es un soak**. En el primer escalón la temperatura sigue subiendo todo el `hold_s`.
- **60 s** solo aplana si al entrar ya se está a menos de ~5 °C del SET.
- A 120–130 °C el PI iba a **~45 %** de duty. Ahí todavía había margen de potencia; la lentitud de esos escalones no demuestra el techo de 190 °C.
- El overshoot del PI, en escalones de 10 °C, fue de **+3,4 °C** una vez y en el resto se quedó por debajo del SET.

`hotplate_heat_trace-3.csv` es el caso contrario y no debe usarse como perfil: entre 110 y 130 °C tardó **7–10 min por cada 10 °C**, con duty ~30 %, y se quedó regulando en **SET − 4 °C** (96, 106, 116 y 126 °C). El lookahead y las ganancias pueden frenar la rampa aun teniendo potencia. Un soak de esa corrida no existe: el `hold_s` corre en el borde inferior de la banda.

`hotplate_heat_trace-2.csv` se quedó ~20 min oscilando en 78 °C dentro del precalentado antiguo. No aporta pendientes de reflow.

### Enfriamiento con aire, al terminar

Pendiente medida al bajar (alarma + enfriamiento). El máximo de la imagen de referencia es 6 °C/s; esta placa está muy por debajo.

| Traza | 130 → 120 | 120 → 110 | 100 → 90 | 60 → 50 | 130 → 50 |
|-------|-----------|-----------|----------|---------|----------|
| heat-trace-3 | 0,19 °C/s | 0,19 °C/s | 0,15 °C/s | 0,05 °C/s | 741 s |
| heat-trace-4 | 0,15 °C/s | 0,16 °C/s | 0,11 °C/s | 0,04 °C/s | 1039 s |

La bajada empinada del perfil de horno **no se puede dibujar**. El ventilador solo actúa al final. De 190 a 183 °C, si la pendiente se pareciera a la de 130 °C (~0,15 °C/s), harían falta unos **45 s** después de cortar el calor. Ese tiempo se suma al TAL y no está medido a 190 °C.

---

## 2. Qué no se copia de la gráfica de horno

| Dato de la gráfica (sin plomo) | En esta placa, con Sn63/Pb37 |
|--------------------------------|------------------------------|
| Liquidus ≈ 217 °C, pico 260 °C | Liquidus **183 °C**. El pico de sensor no puede pasar de **190 °C**. |
| ≤ 8 min hasta el pico | 30 → 100 °C ya cuesta **3 min** a plena potencia. No hay medición de 100 → 190. No usar 8 min como objetivo ni como límite. |
| Subida típica 1–2 °C/s, tope 3 °C/s | Máximo medido **0,75 °C/s** a plena potencia, cerca de 100 °C. El tope de 3 °C/s se cumple solo. |
| Soak largo 150 → 200 °C | Entre 183 y 190 °C solo hay 7 °C. El tramo lento hay que dejarlo **por debajo de 183 °C**. |
| 10 s en el pico y 30 s dentro de 5 °C del pico | Eso limita el estrés a ~260 °C. A 190 °C no se copia como meseta de 10 s. |
| TAL 60–150 s sobre liquidus | Para Sn63/Pb37 el ensayo busca **30–90 s sobre 183 °C en la unión**, medidos con termopar. El `hold_s` del firmware no es ese tiempo: empieza cuando el sensor de la placa entra en SET ± 4 °C. |
| Enfriamiento 2–4 °C/s, máximo 6 | Medido **0,04–0,19 °C/s**. Cumple el máximo por ser mucho más lento. |

---

## 3. Perfil experimental de cuatro escalones

Valores elegidos para HotPanel: temperatura en pasos de 5 °C y meseta en pasos de 30 s. Rampas solo ascendentes. `DLY` `00:00`. Banda `BN` = 4 °C. Dejar `temp_max_c` en **210 °C** en el ensayo: si se pone en 190 °C, una lectura de 190,0 °C dispara `ERROR:7` y corta el calor.

| Escalón | °C | `hold_s` | Por qué este valor |
|---------|----|----------|--------------------|
| R1 | **150** | **120 s** | Meseta análoga al precalentamiento de 60–120 s de la gráfica, en temperatura absoluta de activación del flux. 30 s no aplanaron en trace-4; 120 s da tiempo a que la cola caiga y el tramo se vea plano. 150 + 3,4 °C de overshoot PI ≈ 153 °C, lejos de 183. |
| R2 | **165** | **90 s** | Segundo tramo del soak, todavía 18 °C bajo el liquidus. Cubre el overshoot de +3,4 °C y aun una cola mayor (165 + 16 °C de corte brusco = 181 °C, justo por debajo de 183). 90 s está dentro de la ventana 60–120 s y, a diferencia de 30 s, sí puede estabilizar. |
| R3 | **175** | **60 s** | Hombro antes del pico. No 180 °C: 180 + 3,4 °C ya roza 183 °C y fundiría durante el soak. 60 s basta porque el salto es de 10 °C, igual que los escalones que en trace-4 entraron en banda en ~60 s; la meseta solo remata. |
| R4 | **190** | **90 s** | Pico en el techo declarado. 90 s es el centro del TAL habitual de 30–90 s. No 120–150 s: el enfriamiento medido es tan lento que, si la unión sigue a la placa, otros ~45 s por encima de 183 °C llegan **después** de cortar. |

Rampa de respaldo si el primer ensayo en vacío pasa de 160 °C al final de R1 (la cola de +16 °C del autotune, no la de +3 °C del PI):

| Escalón | °C | `hold_s` |
|---------|----|----------|
| R1 | 140 | 120 s |
| R2 | 160 | 90 s |
| R3 | 190 | 90 s |
| R4 | off | — |

Se pierde el hombro de 175 °C. La curva se parece menos a la silla de la gráfica y gana margen bajo 183 °C.

### Cómo se verá respecto a la gráfica

- De ambiente a 150 °C el approach **no cuenta** dentro de los 120 s. Esos 120 s empiezan al cruzar 146 °C en el sensor de la placa.
- 30 → 100 °C medido: ~3 min a plena potencia. De 100 a 190 °C no hay dato. Aunque la pendiente de 0,7 °C/s se mantuviera, 100 → 190 °C serían ~2 min; junto al techo la pendiente tiene que caer a cero, así que el tramo final será más largo. El total hasta el pico puede superar los 8 min de la gráfica sin que eso indique un fallo.
- La forma esperable es una escalera de cuatro peldaños, no la curva continua del horno. Con estos saltos (15, 10 y 15 °C) se evita tanto la escalera de 10 °C de trace-4 como un único salto hasta 190 °C.
- La bajada será una cola larga (del orden de 12–17 min de 130 a 50 °C en las trazas), no el flanco de la imagen.

### Criterio para aceptar o corregir el ensayo

Primer ciclo **sin pasta**, sensor de la placa. Segundo ciclo con termopar en un pad.

1. Cresta de R1 ≤ 160 °C y de R2 ≤ 175 °C. Si no, usar el perfil de respaldo.
2. Cresta de R3 ≤ 183 °C. Si la pasta funde en R3, bajar R3 a 170 °C.
3. La unión debe pasar de 183 °C. Si no ocurre con R4 a 190 °C, el techo físico no alcanza para esa PCB.
4. Tiempo de la **unión** sobre 183 °C: 30–90 s. Si el enfriamiento lo alarga por encima de 90 s, bajar el `hold_s` de R4 a 60 s. Si no llega a 30 s, subirlo a 120 s. No subir el SET por encima de 190 °C.
5. Si un escalón se queda más de 3 min con duty ≥ 95 % y la temperatura no entra en SET − 4 °C, ese SET es inalcanzable. Hoy `PH_RUN` no tiene timeout: parar a mano.

---

## 4. Cambios de algoritmo pendientes

Ninguno está en el firmware. El orden es el de impacto sobre un perfil con techo en 190 °C.

### 4.1 Consigna de proceso distinta del corte de seguridad

`temp_max_c` (defecto 250 °C) es el corte de `safety_apply_limit`: al llegar, calefactor OFF y `ERROR:7`. No sabe que la planta se equilibra a 190 °C.

Hace falta un techo de consigna, por debajo del corte. Con banda de 4 °C, un SET ≥ 195 °C nunca entra en meseta si el equilibrio es 190 °C: `PH_RUN` sigue con el SSR al 100 % y no hay fin de ciclo. Rechazar en `AT+CFG=R` y en el editor de HotPanel cualquier escalón por encima del techo medido.

El corte de seguridad del ensayo debe quedar **por encima** del pico (210 °C mientras el pico sea 190 °C), no clavado en 190 °C.

### 4.2 Consigna inalcanzable y timeout de `PH_RUN`

`program_runner.c` pasa a `PH_HOLD` solo con `|T − SET| ≤ preheat_band_c`. No hay tiempo máximo de approach.

Si durante un tiempo acotado el duty es ≥ 95 %, la pendiente es casi 0 y `T < SET − BN`, cerrar con un error propio (no `ERROR:7`): cortar el calor. Es el caso de un pico de datasheet a 210–220 °C pedido en esta placa.

### 4.3 El `hold_s` no mide el TAL

La meseta empieza en SET − 4 °C. En trace-3 el minuto de meseta se cumplió **4 °C por debajo** del SET. En trace-4, parte del `hold_s` se gastó todavía subiendo.

Para Sn63/Pb37 el tiempo que importa es el de la unión por encima de **183 °C**, no el del cruce de la banda. Hace falta contarlo en la telemetría (`$HP` o el CSV de HotPlate Studio): instante en que se cruza 183 °C, tiempo por encima, pico y pendiente máxima. Un segundo sensor en la PCB es la medida válida; el PT100 de la placa solo vigila el ciclo.

### 4.4 Autotune lejos del techo

`pid_atune_start` admite el SET hasta `temp_max_c − 10`. Con techo físico 190 °C y `temp_max_c` 250, un autotune a 190 °C exige cruzar 191,5 °C. Si no llega, el SSR queda al 100 % hasta `atune_max_s` (2000 s).

Las trazas útiles están a **100 °C**, con cola de +16 °C. Repetir el autotune en zona con autoridad, del orden de **120–150 °C**, no contra 190 °C. Si el semiperiodo de ON es mucho más largo que el de OFF, o el pico se aplasta con pendiente nula, terminar en `FAIL` sin escribir Kp/Ki en EEPROM.

No hace falta subir `LOOKAHEAD_S_DEFAULT` (15 s). A 0,7 °C/s ya anticipa ~10 °C, y entre 183 y 190 °C solo hay 7 °C. Más horizonte corta antes y aleja la meseta.

### 4.5 Enfriamiento

El aire solo existe al final del ciclo. No hay rampa descendente (el perfil descendente se rechaza con `ERROR:2`) y las trazas muestran 0,04–0,19 °C/s. No planificar una pendiente de 2–4 °C/s. El TAL hay que cerrarlo contando también la bajada libre después del corte.

### 4.6 Fuera de este documento

Más potencia, mejor aislamiento o completar el pico con aire caliente son cambios de hardware o de proceso. No los resuelve el PI. Sin una unión que supere 183 °C con carga, los puntos 4.1–4.5 solo evitan que el ciclo se quede calentando; no crean el perfil de horno.
