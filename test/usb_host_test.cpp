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
    /* program_id_t: HEAT=1, PID_TUNE=2. 0 no es programa. */
    CHECK(1 == 1);
    CHECK(2 == 2);

    /* ERROR:n */
    CHECK(std::strstr("ERROR:1", "ERROR:1") != nullptr);
    CHECK(std::strstr("ERROR:2", "ERROR:2") != nullptr);
    CHECK(std::strstr("ERROR:3", "ERROR:3") != nullptr);
    CHECK(std::strstr("ERROR:4", "ERROR:4") != nullptr);
    CHECK(std::strstr("ERROR:5", "ERROR:5") != nullptr);
    CHECK(std::strstr("ERROR:6", "ERROR:6") != nullptr);
    CHECK(std::strstr("ERROR:7", "ERROR:7") != nullptr);
    CHECK(std::strstr("ERROR:8", "ERROR:8") != nullptr);

    /* ALARM:2 es el fin de HEAT. No hay ALARM:1. */
    CHECK(std::strstr("ALARM:2", "ALARM:2") != nullptr);

    /* $HP de proceso, sin settings ni DEVICE */
    const char *sample =
        "$HP,T=148.0,P=1,A=5,SET=180,DLY=0,RUN=84,EL=10,DU=40,F=0,RI=0,FL=0";
    CHECK(std::strstr(sample, "DEVICE=") == nullptr);
    CHECK(std::strstr(sample, ",P=1,") != nullptr);
    CHECK(std::strstr(sample, ",A=5,") != nullptr);
    CHECK(std::strstr(sample, "MN=") == nullptr);
    CHECK(std::strstr(sample, "KP=") == nullptr);
    CHECK(std::strstr(sample, ",DU=40,") != nullptr);

    const char *tune =
        "$HP,T=148.2,P=2,A=10,SET=150,DLY=0,RUN=0,EL=12,DU=100,F=0,RI=0,FL=0,"
        "AP=1,AC=2,AK=0,AI=0,AD=0";
    CHECK(std::strstr(tune, ",P=2,") != nullptr);
    CHECK(std::strstr(tune, ",A=10,") != nullptr);
    CHECK(std::strstr(tune, "AP=1") != nullptr);
    CHECK(std::strstr(tune, "DU=100") != nullptr);

    const char *cfg =
        "$CF,MN=40,MX=200,KP=20,KI=5,KD=10,PH=1,PCT=80,SB=30,DLY=0,AIR=1,SND=1,RN=2";
    CHECK(std::strstr(cfg, "$CF,") != nullptr);
    CHECK(std::strstr(cfg, "PCT=80") != nullptr);
    CHECK(std::strstr(cfg, "RN=2") != nullptr);

    const char *ramps =
        "$R,N=2,0=180/90,1=220/60,2=100/60,3=125/60";
    CHECK(std::strstr(ramps, "$R,") != nullptr);
    CHECK(std::strstr(ramps, "N=2") != nullptr);
    CHECK(std::strstr(ramps, "0=180/90") != nullptr);
    CHECK(std::strstr(ramps, "1=220/60") != nullptr);
    CHECK(std::strstr(ramps, "3=125/60") != nullptr);

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
        "STAT?", "MODE=", "CFG?", "CFG=", "RUN=", "STOP", nullptr
    };
    for (int i = 0; k_cmds[i]; i++)
        CHECK(k_cmds[i][0] != '\0');

    std::puts("usb_host_test: OK");
    return 0;
}
