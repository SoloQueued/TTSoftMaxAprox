/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module norm_sub4( //compute x - max for 4 signed inputs, saturating at -128
    input  wire [7:0] a_i, b_i, c_i, d_i,
    input  wire [7:0] max_i,
    output wire [7:0] a_o, b_o, c_o, d_o
);

    // x - max is always <= 0 but can reach -255, which does not fit in 8 bits.
    // Compute it in 9 bits and clamp, so e.g. 127 and -128 can't wrap around.
    function automatic [7:0] sat_sub;
        input [7:0] x;
        input [7:0] m;
        reg   [8:0] d;
        begin
            d = {x[7], x} - {m[7], m};
            sat_sub = (d[8] && !d[7]) ? 8'h80 : d[7:0];
        end
    endfunction

    assign a_o = sat_sub(a_i, max_i);
    assign b_o = sat_sub(b_i, max_i);
    assign c_o = sat_sub(c_i, max_i);
    assign d_o = sat_sub(d_i, max_i);

endmodule

`default_nettype wire
