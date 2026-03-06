#define F_CPU 4000000UL

#include <avr/io.h>
#include <util/delay.h>
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"

int main(void)
{
    avr_spi_master_init();

    st7920_init();

    st7920_clear();

    st7920_goto(0, 0);
    st7920_print("Hello World");

    st7920_goto(0, 1);
    st7920_print("ATmega16+ST7920");
    // DDRD |= (1 << PD6);  // Set PD6 as output
    // while(1)
    // {
    //     PORTD ^= (1 << PD6);
    //     _delay_ms(1000);
    //      st7920_update_display();
    // }
}