/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module max4_signed8( //find the maximum of 4 signed 8-bit numbers
    input wire [7:0] a_i, b_i, c_i, d_i,
    output wire [7:0] max_val_o
);
    // Convert inputs to signed for comparison
    wire signed [7:0] a_s = a_i;
    wire signed [7:0] b_s = b_i;
    wire signed [7:0] c_s = c_i;
    wire signed [7:0] d_s = d_i;

    wire signed [7:0] max_ab = (a_s > b_s) ? a_s : b_s;
    wire signed [7:0] max_cd = (c_s > d_s) ? c_s : d_s;
    assign max_val_o = (max_ab > max_cd) ? max_ab : max_cd;
endmodule
