`default_nettype none
`timescale 1ns / 1ps

module tb_exp_lane;

  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb_exp_lane);
    #1;
  end

  reg  [11:0] n_i;
  wire [7:0]  p_o;

  exp_lane dut (
    .n_i(n_i),
    .p_o(p_o)
  );

endmodule
