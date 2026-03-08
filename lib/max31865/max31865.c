#include "max31865.h"
#include <util/delay.h>
#include <math.h>

#define MAX31865_CS_LOW()  MAX31865_CS_PORT &= ~(1 << MAX31865_CS_PIN)
#define MAX31865_CS_HIGH() MAX31865_CS_PORT |= (1 << MAX31865_CS_PIN)

/* Reference resistor (ohms), típico 430 para PT100 */
#define RREF 430.0f

/* PT100 nominal a 0 °C (ohms) */
#define RTD_NOMINAL 100.0f

/* Callendar-Van Dusen (como Adafruit AN709): RTD_A 3.9083e-3, RTD_B -5.775e-7 */
#define RTD_A   (3.9083e-3f)
#define RTD_B   (-5.775e-7f)

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

    uint16_t rtd = ((uint16_t)msb << 8) | lsb;
    if (msb & 0x80u)
        return 0xFFFFu;
    rtd >>= 1;
    return rtd;
}

/* Fórmula temperatura según Adafruit / AN709: C-V con sqrt (T>=0) y polinomio (T<0). */
float max31865_temperature(uint16_t rtd_value) {
    if (rtd_value == 0xFFFFu)
        return -999.0f;

    float Rt = (float)rtd_value / 32768.0f * RREF;
    float Z1, Z2, Z3, Z4, temp;

    Z1 = -RTD_A;
    Z2 = RTD_A * RTD_A - 4.0f * RTD_B;
    Z3 = 4.0f * RTD_B / RTD_NOMINAL;
    Z4 = 2.0f * RTD_B;

    temp = Z2 + (Z3 * Rt);
    temp = (sqrtf(temp) + Z1) / Z4;

    if (temp >= 0.0f)
        return temp;

    /* Para T < 0: polinomio como Adafruit */
    Rt /= RTD_NOMINAL;
    Rt *= 100.0f;
    float rpoly = Rt;
    temp = -242.02f;
    temp += 2.2228f * rpoly;
    rpoly *= Rt;
    temp += 2.5859e-3f * rpoly;
    rpoly *= Rt;
    temp -= 4.8260e-6f * rpoly;
    rpoly *= Rt;
    temp -= 2.8183e-8f * rpoly;
    rpoly *= Rt;
    temp += 1.5243e-10f * rpoly;
    return temp;
}

/* CS bajo = seleccionado (recibe datos); CS alto = deseleccionado. */
void max31865_disable(void) {
    MAX31865_CS_HIGH();
}

void max31865_enable(void) {
    MAX31865_CS_LOW();
}