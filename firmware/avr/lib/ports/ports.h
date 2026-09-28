#ifndef PORTS_H
#define PORTS_H

/* Calefactores: PTC1 = PD7, PTC2 = PD6 */
void ptc_init(void);
void ptc_on(void);       /* ambos a la vez */
void ptc_off(void);
void ptc1_on(void);
void ptc1_off(void);
void ptc2_on(void);
void ptc2_off(void);

/* Bomba de aire / ventilador: FAN = PC0 */
void fan_init(void);
void fan_on(void);
void fan_off(void);
void fan_toggle(void);

/* Buzzer: PD5 */
void buzzer_init(void);
void buzzer_on(void);
void buzzer_off(void);
void buzzer_toggle(void);

#endif
