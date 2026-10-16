/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module norm_sub( //n = x - max for one lane, saturating at -8.0
    input  wire [15:0] x_i,    // signed Q8.8
    input  wire [15:0] max_i,  // signed Q8.8, >= x_i
    output wire [11:0] n_o     // signed Q4.8, in [-8.0, 0]
);

    // x - max can reach -255.99, but e^x * 255 rounds to 0 long before -8, so
    // compute in 17 bits and clamp to -8.0 (-2048) to keep the exp input small.
    wire signed [16:0] d = $signed({x_i[15], x_i}) - $signed({max_i[15], max_i});
    assign n_o = (d < -17'sd2048) ? 12'h800 : d[11:0];

endmodule

`default_nettype wire
