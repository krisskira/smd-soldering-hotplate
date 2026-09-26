#include "max31865.h"
#include <util/delay.h>

#define MAX31865_CS_LOW()  MAX31865_CS_PORT &= ~(1 << MAX31865_CS_PIN)
#define MAX31865_CS_HIGH() MAX31865_CS_PORT |= (1 << MAX31865_CS_PIN)

/* Reference resistor (ohms × 1), típico 430 para PT100 */
#define RREF_OHMS 430u


void max31865_init(void) {
    avr_soft_spi_init();
    MAX31865_CS_DDR |= (1 << MAX31865_CS_PIN);
    MAX31865_CS_HIGH();

    /* 2-wire, filtro 50 Hz, sin auto-conversión (usamos one-shot en cada lectura como Adafruit) */
    uint8_t config = MAX31865_CONFIG_50HZ;
    max31865_write_register(MAX31865_REG_CONFIG, config);
    _delay_ms(100);
}

uint8_t max31865_read_fault_status(void) {
    return max31865_read_register(MAX31865_REG_FAULT_STATUS);
}

void max31865_clear_fault(void) {
    uint8_t t = max31865_read_register(MAX31865_REG_CONFIG);
    t &= (uint8_t)~0x2Cu;
    t |= MAX31865_CONFIG_FAULT_CLEAR;
    max31865_write_register(MAX31865_REG_CONFIG, t);
}

void max31865_prepare_for_read(void) {
    max31865_clear_fault();
    _delay_ms(10);
}

uint8_t max31865_read_register(uint8_t reg) {
    avr_soft_spi_select_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
    avr_soft_spi_transmit(reg & 0x7Fu);
    uint8_t result = avr_soft_spi_transmit(0xFF);
    avr_soft_spi_deselect_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
    return result;
}

void max31865_write_register(uint8_t reg, uint8_t value) {
    avr_soft_spi_select_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
    avr_soft_spi_transmit(reg | 0x80u);
    avr_soft_spi_transmit(value);
    avr_soft_spi_deselect_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
}

/* Lee RTD en modo one-shot (como Adafruit): clear fault, bias on, 1-shot, 65 ms, leer, bias off. */
uint16_t max31865_read_rtd(void) {
    max31865_clear_fault();

    uint8_t config = MAX31865_CONFIG_VBIAS | MAX31865_CONFIG_50HZ;
    max31865_write_register(MAX31865_REG_CONFIG, config);
    _delay_ms(10);

    config |= MAX31865_CONFIG_1SHOT;
    max31865_write_register(MAX31865_REG_CONFIG, config);
    _delay_ms(65);

    /* Una transacción: enviar dirección 0x01 y leer 2 bytes (MSB, LSB) como Adafruit readRegister16 */
    avr_soft_spi_select_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
    avr_soft_spi_transmit(MAX31865_REG_RTD_MSB & 0x7Fu);
    uint8_t msb = avr_soft_spi_transmit(0xFF);
    uint8_t lsb = avr_soft_spi_transmit(0xFF);
    avr_soft_spi_deselect_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);

    /* Desactivar bias para reducir autocalentamiento (como Adafruit) */
    config = MAX31865_CONFIG_50HZ;
    max31865_write_register(MAX31865_REG_CONFIG, config);

    /* El bit de fallo es D0 del registro LSB (el valor RTD son los 15 bits
     * altos). Antes se miraba msb & 0x80, que es un bit de datos: cualquier
     * lectura alta —o un bus sin respuesta, que da 0xFF— se tomaba por fallo. */
    uint16_t rtd = ((uint16_t)msb << 8) | lsb;
    if (rtd & 0x0001u)
        return 0xFFFFu;
    return (uint16_t)(rtd >> 1);
}

/* Temperatura PT100 en °C×10 (fixed-point). Sin soft-float.
 * Rt = ADC/32768 * RREF; T ≈ (Rt - 100) / 0.385
 * T_x10 = 10*(rt_x100/100 - 100)/0.385 = (rt_x100 - 10000)*100/385 */
int16_t max31865_temperature_x10(uint16_t rtd_value) {
    int32_t rt_x100;
    int32_t t_x10;

    if (rtd_value == 0xFFFFu)
        return -9990;

    rt_x100 = (int32_t)(((uint32_t)rtd_value * (uint32_t)RREF_OHMS * 100u) / 32768u);
    t_x10 = ((rt_x100 - 10000L) * 100L) / 385L;
    return (int16_t)t_x10;
}

/* Remove float wrapper to keep soft-float out of the link. */

/* CS bajo = seleccionado (recibe datos); CS alto = deseleccionado. */
void max31865_disable(void) {
    MAX31865_CS_HIGH();
}

void max31865_enable(void) {
    MAX31865_CS_LOW();
}