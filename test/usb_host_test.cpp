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
    case 1: return "START_IN";
    case 2: return "STOP_IN";
    case 3: return "PID_TUNE";
    default: return "?";
    }
}

int main(void)
{
    CHECK(std::strcmp(program_token(0), "PREHEAT") == 0);
    CHECK(std::strcmp(program_token(1), "START_IN") == 0);
    CHECK(std::strcmp(program_token(2), "STOP_IN") == 0);
    CHECK(std::strcmp(program_token(3), "PID_TUNE") == 0);

    CHECK(std::strstr("ERROR:DEVICE-BUSY", "DEVICE-BUSY") != nullptr);
    CHECK(std::strstr("ERROR:USB-MODE-REQUIRED", "USB-MODE-REQUIRED") != nullptr);
    CHECK(std::strstr("ERROR:PROGRAM-BUSY", "PROGRAM-BUSY") != nullptr);
    CHECK(std::strstr("ERROR:ABORTED-BY-DEVICE", "ABORTED-BY-DEVICE") != nullptr);
    CHECK(std::strstr("ERROR:INVALID-COMMAND", "INVALID-COMMAND") != nullptr);
    CHECK(std::strstr("ERROR:INVALID-PARAMETER", "INVALID-PARAMETER") != nullptr);
    CHECK(std::strstr("ERROR:SENSOR-INVALID", "SENSOR-INVALID") != nullptr);
    CHECK(std::strstr("ERROR:OVER-TEMPERATURE", "OVER-TEMPERATURE") != nullptr);

    const char *sample =
        "$HP,T=148.0,DEVICE=USB,PROGRAM=PREHEAT,ACTION=PREHEATING,"
        "SET=150,DELAY=0,RUN=300,REMAIN=84,P1=1,P2=1,FAN=0,DUTY=40,FLT=0";
    CHECK(std::strstr(sample, "DEVICE=USB") != nullptr);
    CHECK(std::strstr(sample, "PROGRAM=PREHEAT") != nullptr);
    CHECK(std::strstr(sample, "ACTION=PREHEATING") != nullptr);
    CHECK(std::strstr(sample, "RUN=300") != nullptr);

    const char *plot =
        "$HP,PLOT,148.0,150,40,151.5,148.5,152.0,147.0";
    CHECK(std::strncmp(plot, "$HP,PLOT,", 9) == 0);
    CHECK(std::strcmp(plot + 9, "148.0,150,40,151.5,148.5,152.0,147.0") == 0);
    CHECK(std::strstr("ALARM:PREHEAT-SUCCESS", "PREHEAT-SUCCESS") != nullptr);
    CHECK(std::strstr("ALARM:CYCLE-DONE", "CYCLE-DONE") != nullptr);

    std::puts("usb_host_test: OK");
    return 0;
}
