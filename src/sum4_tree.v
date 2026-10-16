/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module sum4_tree( //Combinational adder tree (registered).
    input  wire [7:0] a_i, b_i, c_i, d_i,
    output reg  [9:0] sum_o
);
    always @(*) begin // WIP
        sum_o = 10'(a_i) + 10'(b_i) + 10'(c_i) + 10'(d_i);
    end
    
endmodule
