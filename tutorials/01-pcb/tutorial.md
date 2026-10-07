# Fabricar la PCB

La placa de HotPlate no sale de un proceso químico. Se fresa en cobre, en una CNC de escritorio, a partir del plano de KiCad que está en `hardware/pcb/`. El mismo cobre lleva la lógica de control y la etapa de potencia.

## Qué se ve en el taller

La fresa recorre el cobre y deja un surco que aísla cada pista. El plano manda el recorrido: pads redondos, uniones y el contorno de la placa. Cuando la máquina termina, el cobre que no es pista sigue ahí, separado por ese surco. No hay máscara verde ni serigrafía de fábrica; la revisión se hace a ojo y con el microscopio USB, buscando un corte que abra una pista o un puente que una dos redes.

En las fotos de referencia se ve la CNC con la placa sujeta, el detalle de la fresa sobre el cobre, las pistas ya aisladas y la imagen del microscopio.

## Qué lleva esa placa

El plano junta las piezas que el firmware necesita para cerrar el ciclo:

- ATmega16 a 8 MHz, que lee, decide, dibuja la pantalla y atiende el USB.
- MAX31865 y la PT100, para la temperatura.
- MOC3021 y BT136, el relé de estado sólido que enciende las dos resistencias PTC.
- Conector de la ST7920 128×64, el encoder y el buzzer.
- La salida de la bomba de aire, que sopla al final del ciclo.

El fresado deja el cobre listo para soldar esos componentes. Hasta que no están puestos y el sensor responde, el equipo arranca con las salidas apagadas: un fallo de sensor o pasar la temperatura máxima corta el calor.

## Material de esta pieza

- Vídeo: `videos/01-pcb.mp4` y `videos/01-pcb.srt`
- Fotos: `referencias/01-pcb/`
