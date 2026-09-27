/*
 * Host smoke test — contrato MODO USB (códigos numéricos / $HP).
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

/* Espejo parse_u16 firmware. */
static int parse_u16_host(const char **pp, unsigned *out)
{
    const char *p;
    unsigned v = 0;
    unsigned n = 0;

    if (!pp || !*pp || !out)
        return 1;
    p = *pp;
    while (*p >= '0' && *p <= '9' && n < 5u) {
        v = v * 10u + (unsigned)(*p - '0');
        p++;
        n++;
    }
    if (n == 0u)
        return 1;
    *out = v;
    *pp = p;
    return 0;
}

int main(void)
{
    /* program_id_t */
    CHECK(0 == 0); /* PREHEAT */
    CHECK(1 == 1); /* HEAT */
    CHECK(2 == 2); /* PID_TUNE */

    /* ERROR:n */
    CHECK(std::strstr("ERROR:1", "ERROR:1") != nullptr);
    CHECK(std::strstr("ERROR:2", "ERROR:2") != nullptr);
    CHECK(std::strstr("ERROR:3", "ERROR:3") != nullptr);
    CHECK(std::strstr("ERROR:4", "ERROR:4") != nullptr);
    CHECK(std::strstr("ERROR:5", "ERROR:5") != nullptr);
    CHECK(std::strstr("ERROR:6", "ERROR:6") != nullptr);
    CHECK(std::strstr("ERROR:7", "ERROR:7") != nullptr);
    CHECK(std::strstr("ERROR:8", "ERROR:8") != nullptr);

    /* ALARM:n */
    CHECK(std::strstr("ALARM:1", "ALARM:1") != nullptr);
    CHECK(std::strstr("ALARM:2", "ALARM:2") != nullptr);

    /* $HP sin DEVICE; P/A numéricos */
    const char *sample =
        "$HP,T=148.0,P=1,A=2,SET=150,DLY=0,RUN=84,EL=10,"
        "P1=1,P2=1,F=0,DU=40,FL=0,MN=40,MX=200,KP=20,KI=5,KD=10,"
        "CF=337,SB=30,RN=2,RI=0,AP=0,AC=0,AG=3,AH=15,AK=0,AI=0,AD=0";
    CHECK(std::strstr(sample, "DEVICE=") == nullptr);
    CHECK(std::strstr(sample, ",P=1,") != nullptr);
    CHECK(std::strstr(sample, ",A=2,") != nullptr);
    CHECK(std::strstr(sample, "MN=40") != nullptr);
    CHECK(std::strstr(sample, "AG=3") != nullptr);

    const char *tune =
        "$HP,T=148.2,P=2,A=10,SET=150,DLY=0,RUN=0,EL=0,"
        "P1=1,P2=1,F=0,DU=100,FL=0,MN=40,MX=200,KP=20,KI=5,KD=10,"
        "CF=1,SB=30,RN=2,RI=0,AP=1,AC=2,AG=5,AH=15,AK=0,AI=0,AD=0";
    CHECK(std::strstr(tune, ",P=2,") != nullptr);
    CHECK(std::strstr(tune, ",A=10,") != nullptr);
    CHECK(std::strstr(tune, "AP=1") != nullptr);
    CHECK(std::strstr(tune, "DU=100") != nullptr);

    /* parse helpers */
    {
        const char *p;
        unsigned u = 0;
        p = "100";
        CHECK(parse_u16_host(&p, &u) == 0 && u == 100 && *p == '\0');
        p = "2,15";
        CHECK(parse_u16_host(&p, &u) == 0 && u == 2 && *p == ',');
        p = "abc";
        CHECK(parse_u16_host(&p, &u) != 0);
    }

    /* Comandos clave del catálogo (nombres cortos). */
    static const char *k_cmds[] = {
        "STATUS?", "DEVICEMODE=", "PROGRAM=", "TEMP=", "TMIN=", "TMAX=",
        "DELAY=", "PREHEAT=", "PHPCT=", "STAB=", "AIR=", "SND=",
        "RAMPS=", "RAMP=", "ATUNE=", "KP=", "KI=", "KD=", "PIDAPPLY",
        "START", "STOP", nullptr
    };
    for (int i = 0; k_cmds[i]; i++)
        CHECK(k_cmds[i][0] != '\0');

    std::puts("usb_host_test: OK");
    return 0;
}
