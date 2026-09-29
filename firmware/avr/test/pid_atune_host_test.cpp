/*
 * Tests del autotune real (src/services/pid_atune.c) en host.
 *   cd firmware/avr && make pid-atune-host-test
 */
#include "app/app_state.h"
#include "app/app_config.h"
#include "services/pid_atune.h"
#include "services/proto_codes.h"
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
    st->t_set_c = 150;
    st->atune_cycles_target = ATUNE_MIN_CYCLES;
    st->atune_hyst_c_x10 = ATUNE_HYST_C_X10;
    st->atune_max_s = ATUNE_MAX_S_DEFAULT;
    st->sensor.valid = 1;
    st->sensor.temp_c_x10 = 250; /* 25.0 °C */
    st->sensor.fault = 0;
}

static void feed_oscillation(app_state_t *st, uint8_t half_cycles)
{
    /* Alterna T por encima/debajo de banda hyst para completar half-cycles. */
    int16_t set_x10 = (int16_t)(st->t_set_c * 10);
    int16_t hi = (int16_t)(set_x10 + st->atune_hyst_c_x10 + 5);
    int16_t lo = (int16_t)(set_x10 - st->atune_hyst_c_x10 - 5);

    for (uint8_t i = 0; i < half_cycles && st->atune_phase == ATUNE_RUN; i++) {
        host_advance_ms(1000); /* 1 s por medio-ciclo → Tu medible con delay_sec() */
        if (st->atune_relay_on)
            st->sensor.temp_c_x10 = hi;
        else
            st->sensor.temp_c_x10 = lo;
        pid_atune_on_sample(st);
    }
}

static void test_start_rejects_bad_sensor(void)
{
    app_state_t st;
    st_init(&st);
    st.sensor.valid = 0;
    CHECK(pid_atune_start(&st) != 0);
    CHECK(st.atune_phase == ATUNE_IDLE);
}

static void test_start_rejects_setpoint(void)
{
    app_state_t st;
    st_init(&st);
    st.t_set_c = st.temp_max_c; /* > max-10 */
    CHECK(pid_atune_start(&st) != 0);
    CHECK(st.atune_phase == ATUNE_IDLE);

    st.t_set_c = (uint16_t)(st.temp_min_c - 1u);
    CHECK(pid_atune_start(&st) != 0);
}

static void test_start_ok_and_stream_flag(void)
{
    app_state_t st;
    st_init(&st);
    host_set_ms(1000);
    CHECK(pid_atune_start(&st) == 0);
    CHECK(st.atune_phase == ATUNE_RUN);
    CHECK(st.duty_pct == 100);
    CHECK(st.out_state[OUT_PTC1] == 1);
    CHECK(st.out_state[OUT_PTC2] == 1);
}

static void test_cancel(void)
{
    app_state_t st;
    st_init(&st);
    CHECK(pid_atune_start(&st) == 0);
    pid_atune_cancel(&st);
    CHECK(st.atune_phase == ATUNE_IDLE);
    CHECK(st.duty_pct == 0);
    CHECK(st.out_state[OUT_PTC1] == 0);
}

static void test_fail_on_overtemp(void)
{
    app_state_t st;
    st_init(&st);
    CHECK(pid_atune_start(&st) == 0);
    st.sensor.temp_c_x10 = (int16_t)(st.temp_max_c * 10);
    pid_atune_on_sample(&st);
    CHECK(st.atune_phase == ATUNE_FAIL);
}

static void test_complete_and_apply(void)
{
    app_state_t st;
    st_init(&st);
    st.atune_cycles_target = 3;
    host_set_ms(0);
    CHECK(pid_atune_start(&st) == 0);

    /* Necesita s_half_n >= 4 y cycles >= target.
     * Cada cruce hi/lo incrementa half_n. */
    for (int guard = 0; guard < 40 && st.atune_phase == ATUNE_RUN; guard++)
        feed_oscillation(&st, 1);

    CHECK(st.atune_phase == ATUNE_DONE);
    int16_t ak = 0, ai = 0;
    pid_atune_result(&ak, &ai);
    CHECK(ak != 0 || ai != 0);
    pid_atune_apply(&st);
    CHECK(st.atune_phase == ATUNE_IDLE);
    CHECK(st.pid_kp_x10 == ak);
    CHECK(st.pid_ki_x10 == ai);
    CHECK(st.pid_loop == PID_AUTO);
}

static void test_apply_without_done(void)
{
    app_state_t st;
    st_init(&st);
    st.pid_kp_x10 = 20;
    st.atune_phase = ATUNE_RUN;
    pid_atune_apply(&st);
    CHECK(st.pid_kp_x10 == 20); /* no aplica */
    CHECK(st.atune_phase == ATUNE_RUN);
}

int main(void)
{
    test_start_rejects_bad_sensor();
    test_start_rejects_setpoint();
    test_start_ok_and_stream_flag();
    test_cancel();
    test_fail_on_overtemp();
    test_complete_and_apply();
    test_apply_without_done();

    std::puts("pid_atune_host_test: OK");
    return 0;
}
