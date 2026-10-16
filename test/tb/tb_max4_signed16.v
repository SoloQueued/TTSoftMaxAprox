`default_nettype none
`timescale 1ns / 1ps

module tb_max4_signed16;

  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb_max4_signed16);
    #1;
  end

  reg  [15:0] a_i;
  reg  [15:0] b_i;
  reg  [15:0] c_i;
  reg  [15:0] d_i;
  wire [15:0] max_val_o;

  max4_signed16 dut (
    .a_i(a_i),
    .b_i(b_i),
    .c_i(c_i),
    .d_i(d_i),
    .max_val_o(max_val_o)
  );

endmodule
