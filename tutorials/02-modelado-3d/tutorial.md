# Modelar e imprimir la carcasa

La electrónica cabe en una caja que se modela antes de imprimir. Los archivos viven en `mechanical/`: carcasa, base inferior, tapa trasera, tapa con perilla y el difusor de aire. El origen es Fusion 360; lo que se imprime son los 3MF exportados.

## Qué resuelve el modelo

El frente va inclinado para mirar la pantalla y girar la perilla sin levantar la placa caliente. En el modelo se reservan el hueco de la LCD, el eje del encoder y el interruptor. La placa de aluminio no apoya en el plástico: cuatro postes la separan de la caja, de modo que el calor se queda en el aluminio y la carcasa no es la superficie de trabajo.

El lateral impreso lleva un relieve que repite el dibujo de las pistas. No es un adorno suelto: es la misma geometría del proyecto, pasada a la pared de la caja. La perilla se imprime aparte y se monta sobre el encoder.

## Del modelo al equipo cerrado

En la foto de banco se ven las dos cosas a la vez: el sólido abierto en el monitor, con el frente, la ventana y los apoyos, y debajo el equipo ya montado, con la placa de aluminio, los postes y la pantalla encendida. Esa foto es la referencia de que el impreso sigue al modelo, no al revés.

Cuando la caja cierra, el conjunto queda así: aluminio arriba, frente claro con la textura de la impresión, lateral oscuro con el relieve, perilla negra e interruptor. A partir de ahí el calor lo decide el firmware, no la forma de la caja.

## Material de esta pieza

- Vídeo: `videos/02-modelado-3d.mp4` y `videos/02-modelado-3d.srt`
- Fotos: `referencias/02-modelado/`
