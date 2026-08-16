create_clock -name clk -period 10.0 [get_ports clk]
set_clock_uncertainty 0.25 [get_clocks clk]
set_input_delay 2.0 -clock clk [get_ports rst_n]
set_output_delay 2.0 -clock clk [get_ports count*]
