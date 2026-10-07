# El firmware en el ATmega16

El firmware está en C, sin sistema operativo, compilado con avr-gcc. Corre en un ATmega16 a 8 MHz y cabe en los 16 KB de flash. Un planificador cooperativo reparte el tiempo: leer la PT100, calcular la potencia, avanzar el perfil, refrescar la ST7920 y atender la UART. Nada de eso se queda bloqueado esperando.

## Lo que hace un ciclo HEAT

Hay dos programas. HEAT es el ciclo de soldadura. El autoajuste es el otro, y solo se lanza desde el computador. HEAT recorre un perfil de hasta cuatro escalones. Cada escalón tiene temperatura y tiempo de meseta. Los escalones solo suben o se mantienen: un perfil que baja se rechaza antes de arrancar.

El orden, una vez pulsas RUN, es fijo. Si hay espera (`00:00` es inmediato, el tope es 12 horas), cuenta atrás. Luego sube el escalón 1, sostiene su meseta, y sigue con el 2, el 3 y el 4. Al terminar apaga el calor, pita y, si está pedido, enciende el aire hasta la temperatura mínima.

La pantalla lo cuenta en grande. En reposo espera. En espera programada muestra la cuenta. En RUN se ve la temperatura, el escalón, la consigna y el tiempo. En meseta corre el reloj de esa etapa. Al acabar, el aviso. Si Studio toma el mando, la pantalla pasa a USB y la perilla deja de actuar. Nunca hay dos mandos a la vez.

## Cómo regula el calor

La placa tiene inercia. Si se corta la potencia al llegar a la consigna, la temperatura sigue subiendo. El lazo es un PI predictivo: mira hacia adelante y recorta potencia antes. No hay término derivativo. La salida no es un PWM fino del triac a oído: es el tiempo de encendido del relé de estado sólido dentro de una ventana fija.

Las ganancias Kp y Ki viven en la EEPROM, junto con el perfil y los límites. El autoajuste las recalcula y solo las escribe si el ensayo termina. Un corte a medias no pisa los valores anteriores.

Si el sensor no responde, si se alcanza la temperatura máxima, o si la consigna se queda inalcanzable con la potencia al tope, las salidas se apagan.

## Material de esta pieza

- Vídeo: `videos/03-firmware.mp4` y `videos/03-firmware.srt`
- Pantallas: `referencias/03-firmware/`
- Detalle del lazo: `firmware/avr/doc/pid_control.md`
- Orden del ciclo: `firmware/avr/doc/program_flows.md`
