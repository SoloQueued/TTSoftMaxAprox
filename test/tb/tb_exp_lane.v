`default_nettype none
`timescale 1ns / 1ps

module tb_exp_lane;

  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb_exp_lane);
    #1;
  end

  reg  [7:0] x_i;
  wire [7:0] exp_o;

  exp_lane dut (
    .x_i(x_i),
    .exp_o(exp_o)
  );

endmodule
