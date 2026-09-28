/*
 * Tests del lazo PI predictivo (src/services/pid.c) en host.
 *   cd firmware/avr && make pid-host-test
 */
#include "app/app_state.h"
#include "app/app_config.h"
#include "services/pid.h"
#include "host_stubs.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>

#define CHECK(cond) do { \
    if (!(cond)) { \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        std::exit(1); \
    } \
} while (0)

static void st_init(app_state_t *st)
{
    std::memset(st, 0, sizeof(*st));
    st->temp_min_c = TEMP_MIN_C_DEFAULT;
    st->temp_max_c = TEMP_MAX_C_DEFAULT;
    st->t_set_c = 100;
    st->pid_kp_x10 = PID_KP_DEFAULT;
    st->pid_ki_x10 = PID_KI_DEFAULT;
    st->pid_kd_x10 = 0;
    st->sensor.valid = 1;
    st->sensor.temp_c_x10 = 500; /* 50.0 °C */
    st->pid_loop = PID_AUTO;
}

static void sample(app_state_t *st, int16_t t_x10)
{
    st->sensor.temp_c_x10 = t_x10;
    pid_notify_sample();
    pid_tick(st);
    host_advance_ms(1000);
}

static void test_no_kick_on_reset(void)
{
    app_state_t st;
    st_init(&st);
    host_set_ms(0);
    pid_init(&st);
    st.pid_loop = PID_AUTO;
    st.t_set_c = 100;
    st.sensor.temp_c_x10 = 500;
    pid_reset(&st);
    /* Primera muestra: sin D-kick; duty por error predictivo, acotado. */
    sample(&st, 500);
    CHECK(st.duty_pct <= 100);
    CHECK(st.t_ref_x10 >= 500);
}

static void test_cuts_before_setpoint(void)
{
    app_state_t st;
    uint8_t saw_cut = 0;
    st_init(&st);
    host_set_ms(0);
    pid_init(&st);
    st.pid_loop = PID_AUTO;
    st.t_set_c = 100;
    st.pid_kp_x10 = 246;
    st.pid_ki_x10 = 10;
    pid_reset(&st);

    /* Simula subida ~0.7 °C/s desde 70 °C hacia 100 °C. */
    int16_t t = 700;
    for (int i = 0; i < 80; i++) {
        sample(&st, t);
        if (st.duty_pct < 50 && t < 1000) {
            saw_cut = 1;
            break;
        }
        t = (int16_t)(t + 7); /* +0.7 °C/s */
    }
    CHECK(saw_cut);
    CHECK(t < 1000); /* cortó antes de la consigna */
}

static void test_integral_bounded(void)
{
    app_state_t st;
    st_init(&st);
    host_set_ms(0);
    pid_init(&st);
    st.pid_loop = PID_AUTO;
    st.t_set_c = 200;
    pid_reset(&st);
    for (int i = 0; i < 120; i++)
        sample(&st, 500); /* error grande, saturado */
    CHECK(st.duty_pct == 100);
    /* Al acercarse, no debe disparar duty absurdo */
    sample(&st, 1990);
    CHECK(st.duty_pct <= 100);
}

static void test_ref_ramps_toward_set(void)
{
    app_state_t st;
    st_init(&st);
    host_set_ms(0);
    pid_init(&st);
    st.pid_loop = PID_AUTO;
    st.t_set_c = 150;
    pid_reset(&st);
    sample(&st, 500);
    int16_t r0 = st.t_ref_x10;
    sample(&st, 507);
    CHECK(st.t_ref_x10 > r0);
    CHECK(st.t_ref_x10 <= 1500);
}

int main(void)
{
    test_no_kick_on_reset();
    test_cuts_before_setpoint();
    test_integral_bounded();
    test_ref_ramps_toward_set();
    std::printf("pid_host_test: OK\n");
    return 0;
}
