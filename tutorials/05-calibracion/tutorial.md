# Calibrar con HotPlate Studio

Calibrar HotPlate es dejar por escrito los límites, las bandas de meseta y las ganancias del PI, y comprobarlos con un ciclo real. No se hace a ojo en la perilla. Se hace en Studio, con el equipo en línea, y lo que vale queda en la EEPROM.

## 1. Entrar en el equipo

En Conexión se elige el puerto, a 19200 8N1, y se espera `OK` al `AT`. Luego se pasa a modo USB (`AT+MODE=1`). En ese modo la pantalla del equipo muestra USB y la perilla no compite con el computador. El botón Leer ajustes pide `$CF`. Leer rampas pide el perfil.

En la captura de esta sesión el equipo contestó límites de 50 °C y 210 °C, bandas de 4 °C y 6 °C, aire al enfriar activado, y ganancias Kp 24,6 y Ki 0,10. Son los valores de esa placa en ese momento, leídos del equipo, no una tabla universal.

## 2. Límites y bandas

La temperatura mínima es el final del enfriamiento: el aire y el ciclo se dan por terminados al bajar hasta ahí. La máxima es el corte de seguridad: si se alcanza, las salidas se apagan. La consigna de un escalón no puede pasar de 250 °C ni de esa máxima, así que la máxima tiene que quedar por encima del escalón más alto del perfil.

La banda de entrada dice cuándo la temperatura ya está «en meseta» y puede empezar a contar el tiempo. La banda de salida dice hasta dónde puede alejarse sin abortar esa cuenta. Ajustarlas demasiado estrechas hace que una placa con inercia no llegue a contar. Dejarlas anchas da por buena una meseta que todavía se está moviendo.

El retraso de arranque (`00:00` a `12:00`) y el aire al enfriar también se guardan aquí. `00:00` arranca el perfil al momento. El aire sopla en el aviso final y durante el enfriamiento, hasta la mínima.

## 3. Autoajuste del PI

El lazo no usa derivada. Kp y Ki salen de un ensayo: el equipo oscila alrededor de una consigna, mide la respuesta y calcula las ganancias al estilo Ziegler–Nichols para un PI. Studio lanza ese programa, sigue los ciclos en la curva y muestra el resultado.

Las ganancias nuevas se escriben en la EEPROM solo si el ensayo termina. Cortarlo a medias deja las anteriores. Por eso el botón de sobrescribir a mano existe, y por eso no es el camino normal: el camino normal es dejar que el autoajuste acabe.

## 4. Comprobar con un HEAT

Después del ajuste se corre un perfil corto, de escalones que suben, y se mira la curva a 1 Hz. Lo que hay que ver es si la temperatura persigue la consigna sin un sobrepaso largo, si cada meseta llega a contar, y si al final el calor se apaga y el aire enfría. El registro de eventos marca cada cambio de fase. Exportar el CSV deja la corrida fuera de la pantalla, para compararla con la siguiente.

Si durante la subida la potencia se queda al tope y la temperatura no avanza, el firmware corta y avisa. Si el sensor no mide, el calor no tiene por qué estar encendido: el arranque y el fallo dejan las salidas apagadas.

## Material de esta pieza

- Vídeo: `videos/05-calibracion.mp4` y `videos/05-calibracion.srt`
- Capturas de la sesión: `referencias/05-calibracion/`
