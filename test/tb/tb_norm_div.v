`default_nettype none
`timescale 1ns / 1ps

module tb_norm_div;

  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb_norm_div);
    #1;
  end

  reg        clk;
  reg        rst_n;
  reg        start;
  reg  [7:0] p_i;
  reg  [9:0] sum_i;
  wire [7:0] q_o;
  wire       done;

  norm_div dut (
    .clk(clk),
    .rst_n(rst_n),
    .start(start),
    .p_i(p_i),
    .sum_i(sum_i),
    .q_o(q_o),
    .done(done)
  );

endmodule
