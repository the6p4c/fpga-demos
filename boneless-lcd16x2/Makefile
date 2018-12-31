ICEPACK:=C:\\Users\\The6P4C\\.apio\\packages\\toolchain-icestorm\\bin\\icepack.exe
ARACHNE_PNR:=C:\\Users\\The6P4C\\.apio\\packages\\toolchain-icestorm\\bin\\arachne-pnr.exe
YOSYS:=C:\\Users\\The6P4C\\.apio\\packages\\toolchain-icestorm\\bin\\yosys.exe

VERILOG:=top.v cpu.v

all: hardware.bin

clean:
	del cpu.v hardware.blif hardware.asc hardware.bin

upload:
	tinyprog -p hardware.bin

boot:
	tinyprog -b

hardware.bin: hardware.asc
	$(ICEPACK) hardware.asc hardware.bin

hardware.asc: hardware.blif
	$(ARACHNE_PNR) -d 8k -P cm81 -p pins.pcf -o hardware.asc -q hardware.blif

hardware.blif: $(VERILOG)
	$(YOSYS) -p "synth_ice40 -top top -blif hardware.blif" -q $(VERILOG)

cpu.v: cpu.py lcd.py
	set YOSYS=$(subst \\,\,$(YOSYS)) && python cpu.py generate -t v cpu.v

.PHONY: all clean upload boot
