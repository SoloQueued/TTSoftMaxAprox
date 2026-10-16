/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module exp_lane( //LUT-less e^x: 8-segment PWL, slopes are shifts only
    input  wire [11:0] n_i,   // signed Q4.8, x - max, in [-8.0, 0]
    output reg  [7:0]  p_o    // ~255 * e^n, 0..255
);

    // Each segment is y = (n >>> a) +/- (n >>> c) + b: the slope is one or two
    // powers of two, so there is no multiplier and no lookup table. Breakpoints
    // and offsets were fitted to 255*e^x over [-8, 0] for at most 1.84 LSB error.
    wire signed [13:0] n = {{2{n_i[11]}}, n_i};
    reg  signed [13:0] y;

    always @(*) begin
        y = 14'sd0;
        if      (n >=    -76) y = (n >>> 0) - (n >>> 3)      + 254;
        else if (n >=   -159) y = (n >>> 1) + (n >>> 3)      + 236;
        else if (n >=   -257) y = (n >>> 1) - (n >>> 4)      + 205;
        else if (n >=   -337) y = (n >>> 2) + (n >>> 4)      + 174;
        else if (n >=   -453) y = (n >>> 2) - (n >>> 5)      + 141;
        else if (n >=   -654) y = (n >>> 3) - (n >>> 7)      + 95;
        else if (n >=   -903) y = (n >>> 4) - (n >>> 6)      + 49;
        else if (n >=  -1665) y = (n >>> 7) + (n >>> 10)     + 15;
        if (n < -1665) y = 14'sd0;    // 255 * e^x rounds to 0 below -6.5
        p_o = (y < 0) ? 8'd0 : (y > 255) ? 8'd255 : y[7:0];
    end

endmodule

`default_nettype wire
