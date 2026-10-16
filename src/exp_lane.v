/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module exp_lane( //e^n scaled to 8 bits for integer n = x - max <= 0
    input  wire [7:0] x_i,  // signed, <= 0 after max subtraction
    output reg  [7:0] exp_o // round(255 * e^n)
);

    // Inputs are integers, so after subtracting the max there are only seven
    // non-zero results; e^-7 * 255 already rounds to 0. A 7-way select is exact
    // and smaller than a piecewise-linear approximation.
    always @(*) begin
        case (x_i)
            8'h00:   exp_o = 8'd255; //  0
            8'hFF:   exp_o = 8'd94;  // -1
            8'hFE:   exp_o = 8'd35;  // -2
            8'hFD:   exp_o = 8'd13;  // -3
            8'hFC:   exp_o = 8'd5;   // -4
            8'hFB:   exp_o = 8'd2;   // -5
            8'hFA:   exp_o = 8'd1;   // -6
            default: exp_o = 8'd0;   // <= -7 (and positive inputs, which can't occur)
        endcase
    end

endmodule

`default_nettype wire
