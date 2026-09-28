#include "sensor_service.h"
#include "lib/max31865/max31865.h"

void sensor_init(void)
{
    max31865_init();
}

void sensor_tick(sensor_reading_t *out)
{
    uint16_t raw;
    uint8_t msb, lsb, fault;

    if (!out)
        return;

    max31865_prepare_for_read();
    raw = max31865_read_rtd();
    msb = max31865_read_register(MAX31865_REG_RTD_MSB);
    lsb = max31865_read_register(MAX31865_REG_RTD_LSB);
    fault = max31865_read_fault_status();

    out->fault = fault;
    out->rtd_adc = (uint16_t)((((uint16_t)msb << 8) | lsb) >> 1);

    if (raw == 0xFFFFu || fault != 0) {
        out->valid = 0;
        out->temp_c_x10 = 0;
        return;
    }

    out->temp_c_x10 = max31865_temperature_x10(raw);
    out->valid = 1;
}
