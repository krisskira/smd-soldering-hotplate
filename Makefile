############################################
# MCU CONFIG
############################################

MCU = atmega16
F_CPU = 4000000UL

############################################
# TOOLS
############################################

CC = avr-gcc
CXX = avr-g++
OBJCOPY = avr-objcopy
OBJDUMP = avr-objdump
SIZE = avr-size

############################################
# PROGRAMMER
############################################

PROGRAMMER = stk500v1
BAUD = 19200

PORT := $(shell ls /dev/cu.usbserial* 2>/dev/null | head -n 1)

############################################
# FLAGS
############################################

CFLAGS = \
-mmcu=$(MCU) \
-DF_CPU=$(F_CPU) \
-Os \
-flto \
-Wall \
-ffunction-sections \
-fdata-sections \
-I. \
-I./lib

CXXFLAGS = $(CFLAGS)

LDFLAGS = \
-mmcu=$(MCU) \
-Wl,--gc-sections \
-Wl,-Map=build/firmware.map

############################################
# SOURCE FILES
############################################

MAIN = main
BUILD = build

SRC := $(shell find src -name "*.c" -o -name "*.cpp")
# Excluir libs de referencia (Arduino/Adafruit) que no se compilan en este proyecto
LIB_SRC := $(shell find lib -name "*.c" -o -name "*.cpp" | grep -v adafruit)

ALL_SRC := $(SRC) $(LIB_SRC)

OBJ := $(patsubst %.c,$(BUILD)/%.o,$(patsubst %.cpp,$(BUILD)/%.o,$(ALL_SRC)))

TARGET = firmware

############################################
# BUILD RULES
############################################

all: $(BUILD)/$(TARGET).hex

$(BUILD)/$(TARGET).elf: $(OBJ)
	@mkdir -p $(BUILD)
	$(CC) $(OBJ) $(LDFLAGS) -o $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex $< $@
	$(OBJDUMP) -d $< > $(BUILD)/$(TARGET).lss

############################################
# COMPILATION
############################################

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

############################################
# PROGRAM FLASH
############################################

flash: all
	avrdude -c $(PROGRAMMER) -p m16 -P $(PORT) -b $(BAUD) \
	-U flash:w:$(BUILD)/$(TARGET).hex

############################################
# SIZE REPORT
############################################

size: $(BUILD)/$(TARGET).elf
	$(SIZE) -C --mcu=$(MCU) $<

############################################
# FULL PROGRAM
############################################

program: all flash size

############################################
# CLEAN
############################################

clean:
	rm -rf build

############################################

.PHONY: all flash size program clean