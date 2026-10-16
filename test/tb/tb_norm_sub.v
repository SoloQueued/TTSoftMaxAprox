`default_nettype none
`timescale 1ns / 1ps

module tb_norm_sub;

  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb_norm_sub);
    #1;
  end

  reg  [15:0] x_i;
  reg  [15:0] max_i;
  wire [11:0] n_o;

  norm_sub dut (
    .x_i(x_i),
    .max_i(max_i),
    .n_o(n_o)
  );

endmodule
