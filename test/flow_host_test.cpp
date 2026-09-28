/*
 * Validación de flujos HEAT / PREHEAT / PID_TUNE + contrato AT.
 * Espejo de program_flows.md / usb-automation.md (sin MCU).
 *
 *   cd firmware/avr && make flow-host-test
 */
#include "app/app_state.h"
#include "app/app_config.h"
#include "services/program/program.h"
#include "services/proto_codes.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#define CHECK(cond) do { \
    if (!(cond)) { \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        std::exit(1); \
    } \
} while (0)

/* ---------- Mapa PROG_ERR → ERROR:n (at_cmd reply_from_proc) ---------- */
static uint8_t prog_err_to_proto(uint8_t code)
{
    switch (code) {
    case PROG_OK:           return 0;
    case PROG_ERR_SENSOR:   return (uint8_t)PROTO_ERR_SENSOR_INVALID;
    case PROG_ERR_OVERTEMP: return (uint8_t)PROTO_ERR_OVER_TEMPERATURE;
    case PROG_ERR_BUSY:     return (uint8_t)PROTO_ERR_PROGRAM_BUSY;
    case PROG_ERR_FAULT:    return (uint8_t)PROTO_ERR_DEVICE_BUSY;
    default:                return (uint8_t)PROTO_ERR_INVALID_PARAMETER;
    }
}

/* ---------- ACTION $HP ---------- */
static uint8_t action_code(process_phase_t ph, uint8_t atune_run)
{
    if (atune_run)
        return PROTO_ACTION_TUNING;
    return (uint8_t)ph;
}

/* ---------- Simulador de fases (contrato documental) ---------- */
enum FlowEvt {
    EVT_TICK_SEC = 1,
    EVT_BAND_OK,      /* T en banda de stabilize */
    EVT_RAMPS_DONE,
    EVT_ALARM_TIMEOUT,
    EVT_COOL_DONE,
    EVT_STOP,
    EVT_ACK
};

struct FlowSim {
    program_id_t program;
    process_phase_t phase;
    uint8_t preheat_en;
    uint8_t delay_s;
    uint8_t ramp_n;
    uint8_t alarm_n;   /* último ALARM emitido, 0 = ninguno */
    uint8_t active;
};

static void flow_reset(FlowSim *f, program_id_t p)
{
    std::memset(f, 0, sizeof(*f));
    f->program = p;
    f->phase = PH_IDLE;
    f->preheat_en = 1;
    f->ramp_n = 2;
}

static int flow_start(FlowSim *f)
{
    if (f->active)
        return PROG_ERR_BUSY;
    if (f->program == PROG_HEAT && f->ramp_n < 1)
        return PROG_ERR_PARAM;

    f->active = 1;
    f->alarm_n = 0;

    if (f->program == PROG_PID_TUNE) {
        f->phase = PH_IDLE; /* fase proceso idle; ACTION override = TUNING */
        return PROG_OK;
    }
    /* HEAT */
    if (f->delay_s > 0)
        f->phase = PH_DELAY;
    else if (f->preheat_en)
        f->phase = PH_PREHEAT;
    else
        f->phase = PH_RUN;
    return PROG_OK;
}

static void flow_enter_alarm(FlowSim *f, uint8_t alarm)
{
    f->phase = PH_ALARM;
    f->alarm_n = alarm;
}

static void flow_event(FlowSim *f, FlowEvt e)
{
    if (!f->active && e != EVT_STOP)
        return;

    if (e == EVT_STOP) {
        if (f->program == PROG_HEAT
            && (f->phase == PH_DELAY || f->phase == PH_PREHEAT
                || f->phase == PH_STABILIZE || f->phase == PH_RUN)) {
            flow_enter_alarm(f, (uint8_t)PROTO_ALARM_DONE);
            return;
        }
        f->phase = PH_IDLE;
        f->active = 0;
        return;
    }

    switch (f->program) {
    case PROG_HEAT:
        if (f->phase == PH_DELAY && e == EVT_TICK_SEC && f->delay_s == 0) {
            f->phase = f->preheat_en ? PH_PREHEAT : PH_RUN;
        } else if (f->phase == PH_PREHEAT && e == EVT_BAND_OK)
            f->phase = PH_STABILIZE;
        else if (f->phase == PH_STABILIZE && e == EVT_BAND_OK)
            f->phase = PH_RUN;
        else if (f->phase == PH_RUN && e == EVT_RAMPS_DONE)
            flow_enter_alarm(f, (uint8_t)PROTO_ALARM_DONE);
        else if (f->phase == PH_ALARM
                 && (e == EVT_ALARM_TIMEOUT || e == EVT_ACK))
            f->phase = PH_COOLDOWN;
        else if (f->phase == PH_COOLDOWN && e == EVT_COOL_DONE) {
            f->phase = PH_DONE;
            f->active = 0;
        }
        break;

    case PROG_PID_TUNE:
        if (e == EVT_STOP) {
            f->phase = PH_IDLE;
            f->active = 0;
        }
        break;

    default:
        break;
    }
}

static void test_enums_aligned(void)
{
    CHECK((int)PH_IDLE == 0);
    CHECK((int)PH_FAULT == 9);
    CHECK((int)PROG_HEAT == 1);
    CHECK((int)PROG_PID_TUNE == 2);
    CHECK((int)ATUNE_IDLE == 0);
    CHECK((int)ATUNE_RUN == 1);
    CHECK((int)ATUNE_DONE == 2);
    CHECK((int)ATUNE_FAIL == 3);
    CHECK(PROTO_ACTION_TUNING == 10u);
    CHECK(PROTO_ALARM_DONE == 2);
}

static void test_prog_err_map(void)
{
    CHECK(prog_err_to_proto(PROG_OK) == 0);
    CHECK(prog_err_to_proto(PROG_ERR_SENSOR) == PROTO_ERR_SENSOR_INVALID);
    CHECK(prog_err_to_proto(PROG_ERR_PARAM) == PROTO_ERR_INVALID_PARAMETER);
    CHECK(prog_err_to_proto(PROG_ERR_BUSY) == PROTO_ERR_PROGRAM_BUSY);
    CHECK(prog_err_to_proto(PROG_ERR_FAULT) == PROTO_ERR_DEVICE_BUSY);
}

static void test_heat_with_delay_and_preheat(void)
{
    FlowSim f;
    flow_reset(&f, PROG_HEAT);
    f.delay_s = 1;
    f.preheat_en = 1;
    CHECK(flow_start(&f) == PROG_OK);
    CHECK(f.phase == PH_DELAY);

    f.delay_s = 0;
    flow_event(&f, EVT_TICK_SEC);
    CHECK(f.phase == PH_PREHEAT);

    flow_event(&f, EVT_BAND_OK);
    CHECK(f.phase == PH_STABILIZE);
    flow_event(&f, EVT_BAND_OK);
    CHECK(f.phase == PH_RUN);

    flow_event(&f, EVT_RAMPS_DONE);
    CHECK(f.phase == PH_ALARM);
    CHECK(f.alarm_n == PROTO_ALARM_DONE);

    flow_event(&f, EVT_ACK);
    CHECK(f.phase == PH_COOLDOWN);
    flow_event(&f, EVT_COOL_DONE);
    CHECK(f.phase == PH_DONE);
}

static void test_heat_skip_preheat(void)
{
    FlowSim f;
    flow_reset(&f, PROG_HEAT);
    f.delay_s = 0;
    f.preheat_en = 0;
    CHECK(flow_start(&f) == PROG_OK);
    CHECK(f.phase == PH_RUN);
}

static void test_heat_no_ramps(void)
{
    FlowSim f;
    flow_reset(&f, PROG_HEAT);
    f.ramp_n = 0;
    CHECK(flow_start(&f) == PROG_ERR_PARAM);
    CHECK(prog_err_to_proto(PROG_ERR_PARAM) == PROTO_ERR_INVALID_PARAMETER);
}

static void test_heat_stop_during_run(void)
{
    FlowSim f;
    flow_reset(&f, PROG_HEAT);
    f.preheat_en = 0;
    CHECK(flow_start(&f) == PROG_OK);
    CHECK(f.phase == PH_RUN);
    flow_event(&f, EVT_STOP);
    CHECK(f.phase == PH_ALARM);
    CHECK(f.alarm_n == PROTO_ALARM_DONE);
}

static void test_pid_tune_at_sequence(void)
{
    /* Secuencia documentada: MODE → RUN=2 → CFG=A → STOP */
    static const char *seq[] = {
        "AT+MODE=1",
        "AT+CFG=T,5,15,1200",
        "AT+RUN=2,150,5,15,1200",
        "AT+CFG=A",
        "AT+STOP",
        nullptr
    };
    for (int i = 0; seq[i]; i++) {
        CHECK(std::strncmp(seq[i], "AT", 2) == 0);
        CHECK(std::strlen(seq[i]) < AT_LINE_MAX);
    }

    /* Regla consigna PID_TUNE: [TMIN .. TMAX-10] */
    uint16_t tmin = 40, tmax = 200, tset;
    tset = 150;
    CHECK(tset >= tmin && tset <= (uint16_t)(tmax - 10u));
    tset = 195;
    CHECK(tset > (uint16_t)(tmax - 10u)); /* debe rechazarse → ERROR:2 */

    FlowSim f;
    flow_reset(&f, PROG_PID_TUNE);
    CHECK(flow_start(&f) == PROG_OK);
    CHECK(action_code(f.phase, 1) == PROTO_ACTION_TUNING);
    flow_event(&f, EVT_STOP);
    CHECK(!f.active);
    CHECK(action_code(PH_IDLE, 0) == (uint8_t)PH_IDLE);
}

static void test_at_catalog_length(void)
{
    static const char *cmds[] = {
        "AT+STAT?", "AT+MODE=1", "AT+MODE=0",
        "AT+CFG=S,40,250",
        "AT+CFG=H,1,80,30,0,1,1",
        "AT+CFG=H,1,100,3600,3600,1,1",
        "AT+CFG=P,120,40,10",
        "AT+CFG=R,0,180,90",
        "AT+CFG=R?",
        "AT+CFG=A",
        "AT+CFG?",
        "AT+RUN=1",
        "AT+RUN=2,150,5,15",
        "AT+STOP",
        nullptr
    };
    for (int i = 0; cmds[i]; i++)
        CHECK(std::strlen(cmds[i]) < AT_LINE_MAX);
}

int main(void)
{
    test_enums_aligned();
    test_prog_err_map();
    test_heat_with_delay_and_preheat();
    test_heat_skip_preheat();
    test_heat_no_ramps();
    test_heat_stop_during_run();
    test_pid_tune_at_sequence();
    test_at_catalog_length();

    std::puts("flow_host_test: OK");
    return 0;
}
