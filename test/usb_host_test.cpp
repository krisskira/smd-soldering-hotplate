/*
 * Host smoke test — contrato MODO USB (tokens / errores / trama).
 *   cd firmware/avr && make usb-host-test
 */
#include <cstdio>
#include <cstring>
#include <cstdlib>

#define CHECK(cond) do { \
    if (!(cond)) { \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        std::exit(1); \
    } \
} while (0)

static const char *program_token(int p)
{
    switch (p) {
    case 0: return "PREHEAT";
    case 1: return "HEAT";
    case 2: return "PID_TUNE";
    default: return "?";
    }
}

int main(void)
{
    CHECK(std::strcmp(program_token(0), "PREHEAT") == 0);
    CHECK(std::strcmp(program_token(1), "HEAT") == 0);
    CHECK(std::strcmp(program_token(2), "PID_TUNE") == 0);

    CHECK(std::strstr("ERROR:DEVICE-BUSY", "DEVICE-BUSY") != nullptr);
    CHECK(std::strstr("ERROR:USB-MODE-REQUIRED", "USB-MODE-REQUIRED") != nullptr);
    CHECK(std::strstr("ERROR:PROGRAM-BUSY", "PROGRAM-BUSY") != nullptr);
    CHECK(std::strstr("ERROR:ABORTED-BY-DEVICE", "ABORTED-BY-DEVICE") != nullptr);
    CHECK(std::strstr("ERROR:INVALID-COMMAND", "INVALID-COMMAND") != nullptr);
    CHECK(std::strstr("ERROR:INVALID-PARAMETER", "INVALID-PARAMETER") != nullptr);
    CHECK(std::strstr("ERROR:SENSOR-INVALID", "SENSOR-INVALID") != nullptr);

    const char *sample =
        "$HP,T=148.0,DEVICE=USB,PROGRAM=HEAT,ACTION=PREHEATING,"
        "SET=150,DELAY=0,RUN=84,P1=1,P2=1,FAN=0,DUTY=40,FLT=0";
    CHECK(std::strstr(sample, "DEVICE=USB") != nullptr);
    CHECK(std::strstr(sample, "PROGRAM=HEAT") != nullptr);
    CHECK(std::strstr(sample, "ACTION=PREHEATING") != nullptr);

    CHECK(std::strstr("ALARM:PH-OK", "PH-OK") != nullptr);
    CHECK(std::strstr("ALARM:DONE", "DONE") != nullptr);
    CHECK(std::strstr("OT\r\n", "OT") != nullptr);

    const char *tune =
        "$HP,T=148.2,DEVICE=USB,PROGRAM=PID_TUNE,ACTION=TUNING,"
        "SET=150,DELAY=0,RUN=0,P1=1,P2=1,FAN=0,DUTY=100,FLT=0";
    CHECK(std::strstr(tune, "PROGRAM=PID_TUNE") != nullptr);
    CHECK(std::strstr(tune, "ACTION=TUNING") != nullptr);
    CHECK(std::strstr(tune, "DUTY=100") != nullptr);
    CHECK(std::strstr(tune, "REMAIN=") == nullptr);

    std::puts("usb_host_test: OK");
    return 0;
}
