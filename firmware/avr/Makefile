############################################
# MCU CONFIG
############################################

MCU = atmega16
F_CPU = 8000000UL

############################################
# TOOLS
############################################

CC = avr-gcc
CXX = avr-g++
OBJCOPY = avr-objcopy
OBJDUMP = avr-objdump
SIZE = avr-size
LD = $(CC)

############################################
# PROGRAMMER
############################################

PROGRAMMER = stk500v1
BAUD = 19200
PORT := $(shell ls /dev/cu.usbserial* 2>/dev/null | head -n 1)

############################################
# FLAGS — un solo firmware (HOME + USB/AT + pipeline)
# Fuentes enlazadas: font5x7 + font8x12 (temperatura) + font_icons.
############################################

# Con LTO el código se genera al enlazar: OPTFLAGS va también en LDFLAGS.
# -mcall-prologues / -mrelax / -fno-inline-small-functions: ~800 B menos.
OPTFLAGS = \
-Os \
-flto \
-mcall-prologues \
-mrelax \
-fno-inline-small-functions

CFLAGS = \
-mmcu=$(MCU) \
-DF_CPU=$(F_CPU) \
$(OPTFLAGS) \
-Wall \
-ffunction-sections \
-fdata-sections \
-I. \
-I./src \
-I./src/ui \
-I./src/ui/core \
-I./lib \
-I./config

CXXFLAGS = $(CFLAGS) -std=c++11 -fno-exceptions -fno-rtti

LDFLAGS = \
-mmcu=$(MCU) \
$(OPTFLAGS) \
-Wl,--gc-sections \
-Wl,-Map=build/firmware.map

############################################
# SOURCE FILES
# features/parked/ no se enlaza. Ver features/parked/README.md
############################################

BUILD = build

SRC := \
	src/main.c \
	src/ui/core/ui_text.c \
	src/ui/core/ui_components.c \
	src/ui/home_view.c \
	src/ui/ui_router.c \
	src/services/buzzer_seq.c \
	src/services/outputs.c \
	src/services/cfg_store.c \
	src/services/program/program_runner.c \
	src/services/pid.c \
	src/services/pid_atune.c \
	src/services/sensor_service.c \
	src/services/safety.c \
	src/services/device_session.c \
	src/services/proto_tokens.c \
	src/services/proto_emit.c \
	src/services/at_cmd.c \
	src/services/telemetry.c \
	lib/i18n/i18n.c

LIB_SRC := $(shell find lib \( -path '*/avr_spi/*' -o -path '*/avr_soft_spi/*' -o -path '*/avr_delay/*' -o -path '*/avr_uart/*' -o -path '*/encoder/*' -o -path '*/st7920/*' -o -path '*/ports/*' -o -path '*/fonts/*' -o -path '*/max31865/*' \) -name '*.c' | tr '\n' ' ')

ALL_SRC := $(SRC) $(LIB_SRC)
OBJ := $(patsubst %.c,$(BUILD)/%.o,$(ALL_SRC))
TARGET = firmware

# LTO + avr-ld: dos `make` a la vez corrompen .o → "ELF section name out of range".
# Escritura atómica de objetos + sin paralelismo en este Makefile.
.NOTPARALLEL:

all: $(BUILD)/$(TARGET).hex

$(BUILD)/$(TARGET).elf: $(OBJ)
	@mkdir -p $(BUILD)
	$(LD) $(OBJ) $(LDFLAGS) -o $@.tmp
	mv -f $@.tmp $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex $< $@
	$(OBJDUMP) -d $< > $(BUILD)/$(TARGET).lss

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@.tmp
	mv -f $@.tmp $@

$(BUILD)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@.tmp
	mv -f $@.tmp $@

flash: all
	avrdude -c $(PROGRAMMER) -p m16 -P $(PORT) -b $(BAUD) \
	-U flash:w:$(BUILD)/$(TARGET).hex

size: $(BUILD)/$(TARGET).elf
	$(SIZE) -C --mcu=$(MCU) $<

program: all flash size

clean:
	rm -rf build

.PHONY: all flash size program clean test usb-host-test flow-host-test pid-atune-host-test pid-host-test

# Contrato UART + catálogo AT
usb-host-test:
	@mkdir -p build
	g++ -std=c++11 -Wall -I. -I./src -I./src/services -I./src/app \
		-o build/usb_host_test test/usb_host_test.cpp
	./build/usb_host_test

# Flujos HEAT / PREHEAT / PID_TUNE (máquina de fases + AT)
flow-host-test:
	@mkdir -p build
	g++ -std=c++11 -Wall -I. -I./src -I./src/services -I./src/app \
		-o build/flow_host_test test/flow_host_test.cpp
	./build/flow_host_test

# Autotune real (pid_atune.c) con stubs host
pid-atune-host-test:
	@mkdir -p build/test
	gcc -std=c11 -Wall -DHOST_TEST \
		-I. -I./src -I./src/services -I./src/app -I./lib \
		-c src/services/pid_atune.c -o build/test/pid_atune_host.o
	gcc -std=c11 -Wall -DHOST_TEST \
		-I. -I./src -I./src/services -I./src/app -I./lib \
		-c test/host_stubs.c -o build/test/host_stubs.o
	g++ -std=c++11 -Wall -DHOST_TEST \
		-I. -I./src -I./src/services -I./src/app -I./lib \
		-c test/pid_atune_host_test.cpp -o build/test/pid_atune_host_test.o
	g++ -o build/pid_atune_host_test \
		build/test/pid_atune_host.o build/test/host_stubs.o \
		build/test/pid_atune_host_test.o
	./build/pid_atune_host_test

# Lazo PI predictivo (pid.c) con stubs host
pid-host-test:
	@mkdir -p build/test
	gcc -std=c11 -Wall -DHOST_TEST -DPID_HOST_TEST \
		-I. -I./src -I./src/services -I./src/app -I./lib \
		-c src/services/pid.c -o build/test/pid_host.o
	gcc -std=c11 -Wall -DHOST_TEST -DPID_HOST_TEST \
		-I. -I./src -I./src/services -I./src/app -I./lib \
		-c test/host_stubs.c -o build/test/host_stubs_pid.o
	g++ -std=c++11 -Wall -DHOST_TEST -DPID_HOST_TEST \
		-I. -I./src -I./src/services -I./src/app -I./lib \
		-c test/pid_host_test.cpp -o build/test/pid_host_test.o
	g++ -o build/pid_host_test \
		build/test/pid_host.o build/test/host_stubs_pid.o \
		build/test/pid_host_test.o
	./build/pid_host_test

test: usb-host-test flow-host-test pid-atune-host-test pid-host-test
	@echo "all host tests: OK"

# Capturas de HotPanel con el home_view.c real → doc/img/hotpanel/*.png
UI_SCREENS_SRC := tools/ui_screens/screens.c src/ui/home_view.c \
	src/ui/core/ui_text.c src/ui/core/ui_components.c lib/i18n/i18n.c \
	lib/st7920/st7920_text.c lib/fonts/font.c lib/fonts/font5x7.c \
	lib/fonts/font8x12.c lib/fonts/font_icons.c

ui-screens:
	@mkdir -p build/ui_screens doc/img/hotpanel
	gcc -std=c11 -Wall -Wno-unused-function -I./tools/ui_screens -I. -I./src \
		-I./src/ui -I./src/ui/core -I./lib -I./config \
		-o build/ui_screens/screens $(UI_SCREENS_SRC)
	./build/ui_screens/screens build/ui_screens
	python3 tools/ui_screens/pbm2png.py build/ui_screens doc/img/hotpanel

.PHONY: ui-screens
