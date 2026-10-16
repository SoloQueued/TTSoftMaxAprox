/*
 * Copyright (c) 2024 Q Le
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module norm_div( //shared restoring divider: q = min(255, floor(p * 256 / sum))
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,  // one-cycle pulse; latches p_i
    input  wire [7:0] p_i,    // one lane's exponential
    input  wire [9:0] sum_i,  // sum of all four exponentials, held stable
    output wire [7:0] q_o,    // normalised probability, 0..255
    output reg        done    // one-cycle pulse when q_o is ready
);

    // p is one of the four terms of sum, so p <= sum and the running
    // remainder stays below sum (< 1024): 11 bits is enough. One quotient
    // bit per clock, 8 clocks per lane, one divider shared by all lanes.
    reg [10:0] rem;
    reg [7:0]  q;
    reg [3:0]  cnt;

    wire [11:0] dbl = {rem, 1'b0};
    wire        ge  = (dbl >= {2'b00, sum_i});

    // When p == sum (every other lane is 0) every step subtracts, so q ends at 255.
    assign q_o = q;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rem  <= 11'd0;
            q    <= 8'd0;
            cnt  <= 4'd0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start) begin
                rem <= {3'b000, p_i};
                q   <= 8'd0;
                cnt <= 4'd8;
            end else if (cnt != 4'd0) begin
                rem <= ge ? (dbl[10:0] - {1'b0, sum_i}) : dbl[10:0];
                q   <= {q[6:0], ge};
                cnt <= cnt - 4'd1;
                if (cnt == 4'd1) done <= 1'b1;
            end
        end
    end

endmodule

`default_nettype wire
