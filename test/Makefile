# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES ?= project.v max4_signed8.v norm_sub4.v exp_lane.v sum4_tree.v norm_div.v
TB_FILE ?= tb.v
TOPLEVEL ?= tb
COCOTB_TEST_MODULES ?= test

.DEFAULT_GOAL := sim

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/$(TB_FILE)

.PHONY: test-all test-max4 test-norm-sub4 test-exp-lane test-sum4-tree test-norm-div

test-all: test-max4 test-norm-sub4 test-exp-lane test-sum4-tree test-norm-div

test-max4:
	$(MAKE) SIM_BUILD="sim_build/max4" PROJECT_SOURCES="max4_signed8.v" TB_FILE="tb/tb_max4_signed8.v" TOPLEVEL="tb_max4_signed8" COCOTB_TEST_MODULES="test_max4_signed8" sim

test-norm-sub4:
	$(MAKE) SIM_BUILD="sim_build/norm_sub4" PROJECT_SOURCES="norm_sub4.v" TB_FILE="tb/tb_norm_sub4.v" TOPLEVEL="tb_norm_sub4" COCOTB_TEST_MODULES="test_norm_sub4" sim

test-exp-lane:
	$(MAKE) SIM_BUILD="sim_build/exp_lane" PROJECT_SOURCES="exp_lane.v" TB_FILE="tb/tb_exp_lane.v" TOPLEVEL="tb_exp_lane" COCOTB_TEST_MODULES="test_exp_lane" sim

test-sum4-tree:
	$(MAKE) SIM_BUILD="sim_build/sum4_tree" PROJECT_SOURCES="sum4_tree.v" TB_FILE="tb/tb_sum4_tree.v" TOPLEVEL="tb_sum4_tree" COCOTB_TEST_MODULES="test_sum4_tree" sim

test-norm-div:
	$(MAKE) SIM_BUILD="sim_build/norm_div" PROJECT_SOURCES="norm_div.v" TB_FILE="tb/tb_norm_div.v" TOPLEVEL="tb_norm_div" COCOTB_TEST_MODULES="test_norm_div" sim

include $(shell cocotb-config --makefiles)/Makefile.sim
