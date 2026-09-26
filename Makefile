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
# Flash gates: NO_PID_ATUNE, UI_NO_ICONS (sin iconos en filas), sin font6x8
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
-I./config \
-DNO_FONT_6X8 \
-DUI_NO_ICONS \
-DNO_PID_ATUNE

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
	src/ui/core/ui_window.c \
	src/ui/core/ui_components.c \
	src/ui/core/ui_display.c \
	src/ui/home_view.c \
	src/ui/usb_view.c \
	src/ui/settings_view.c \
	src/ui/ui_router.c \
	src/services/buzzer_seq.c \
	src/services/outputs.c \
	src/services/cfg_store.c \
	src/services/program/program_runner.c \
	src/services/pid.c \
	src/services/sensor_service.c \
	src/services/safety.c \
	src/services/device_session.c \
	src/services/at_cmd.c \
	src/services/telemetry.c \
	lib/i18n/i18n.c

# Sin font6x8_bold (flash). font8x12 (temperatura USB) y font_icons (solo ENTER)
# sí entran. pid_atune.c stub via NO_PID_ATUNE.
LIB_SRC := $(shell find lib \( -path '*/avr_spi/*' -o -path '*/avr_soft_spi/*' -o -path '*/avr_delay/*' -o -path '*/avr_uart/*' -o -path '*/encoder/*' -o -path '*/st7920/*' -o -path '*/ports/*' -o -path '*/fonts/*' -o -path '*/max31865/*' \) ! -name 'font6x8_bold.c' -name '*.c' | tr '\n' ' ')

ALL_SRC := $(SRC) $(LIB_SRC)
OBJ := $(patsubst %.c,$(BUILD)/%.o,$(ALL_SRC))
TARGET = firmware

all: $(BUILD)/$(TARGET).hex

$(BUILD)/$(TARGET).elf: $(OBJ)
	@mkdir -p $(BUILD)
	$(LD) $(OBJ) $(LDFLAGS) -o $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex $< $@
	$(OBJDUMP) -d $< > $(BUILD)/$(TARGET).lss

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

flash: all
	avrdude -c $(PROGRAMMER) -p m16 -P $(PORT) -b $(BAUD) \
	-U flash:w:$(BUILD)/$(TARGET).hex

size: $(BUILD)/$(TARGET).elf
	$(SIZE) -C --mcu=$(MCU) $<

program: all flash size

clean:
	rm -rf build

.PHONY: all flash size program clean usb-host-test

usb-host-test:
	@mkdir -p build
	g++ -std=c++11 -Wall -o build/usb_host_test test/usb_host_test.cpp
	./build/usb_host_test
