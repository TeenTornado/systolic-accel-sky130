LIB_URL := https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

.PHONY: all lib sim lint ppa clean

all: lint sim ppa

lib: lib/hd_tt.lib

lib/hd_tt.lib:
	mkdir -p lib
	curl -sSL -o $@ $(LIB_URL)

sim:
	python3 tb/run_tests.py

lint:
	mkdir -p build
	iverilog -g2005 -Wall -s systolic_array -o build/lint.vvp rtl/pe.v rtl/systolic_array.v
	yosys -q -p "read_verilog rtl/pe.v rtl/systolic_array.v; hierarchy -top systolic_array; proc; check -assert"

ppa: lib
	python3 scripts/ppa_sweep.py

clean:
	rm -rf build sim_build results/*.log
