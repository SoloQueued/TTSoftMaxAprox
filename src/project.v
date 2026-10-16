/*
 * Copyright (c) 2024 DerekTDLe
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_nonlut_softmax (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Datapath: max -> x - max (saturating) -> e^n (exact for integers) -> sum
  //           -> one shared divider, p_i * 256 / sum, streamed out lane by lane.
  localparam S_IDLE     = 3'd0;
  localparam S_LOAD     = 3'd1;
  localparam S_SUM      = 3'd2;
  localparam S_DIV      = 3'd3;
  localparam S_DIV_WAIT = 3'd4;
  localparam S_DONE     = 3'd5;

  reg [2:0] state;
  reg [1:0] idx;      // input lane while loading, output lane while dividing

  reg [7:0] x0_reg;
  reg [7:0] x1_reg;
  reg [7:0] x2_reg;
  reg [7:0] x3_reg;

  reg [9:0] sum_reg;

  reg       div_start;
  reg [7:0] out_reg;
  reg       valid_reg;
  reg       done_reg;

  wire [7:0] max_val_w;
  wire [7:0] n0_w, n1_w, n2_w, n3_w;
  wire [7:0] p0_w, p1_w, p2_w, p3_w;
  wire [9:0] sum_w;
  wire [7:0] q_w;
  wire       div_done_w;

  max4_signed8 u_max4 (
      .a_i(x0_reg),
      .b_i(x1_reg),
      .c_i(x2_reg),
      .d_i(x3_reg),
      .max_val_o(max_val_w)
  );

  norm_sub4 u_norm_sub4 (
      .a_i(x0_reg),
      .b_i(x1_reg),
      .c_i(x2_reg),
      .d_i(x3_reg),
      .max_i(max_val_w),
      .a_o(n0_w),
      .b_o(n1_w),
      .c_o(n2_w),
      .d_o(n3_w)
  );

  exp_lane u_exp0 (.x_i(n0_w), .exp_o(p0_w));
  exp_lane u_exp1 (.x_i(n1_w), .exp_o(p1_w));
  exp_lane u_exp2 (.x_i(n2_w), .exp_o(p2_w));
  exp_lane u_exp3 (.x_i(n3_w), .exp_o(p3_w));

  sum4_tree u_sum4 (
      .a_i(p0_w),
      .b_i(p1_w),
      .c_i(p2_w),
      .d_i(p3_w),
      .sum_o(sum_w)
  );

  // The inputs stay in x*_reg for the whole transaction, so each lane's
  // exponential can be picked straight off the combinational path.
  reg [7:0] p_sel;
  always @(*) begin
    case (idx)
      2'd0:    p_sel = p0_w;
      2'd1:    p_sel = p1_w;
      2'd2:    p_sel = p2_w;
      default: p_sel = p3_w;
    endcase
  end

  norm_div u_div (
      .clk(clk),
      .rst_n(rst_n),
      .start(div_start),
      .p_i(p_sel),
      .sum_i(sum_reg),
      .q_o(q_w),
      .done(div_done_w)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state     <= S_IDLE;
      idx       <= 2'd0;
      x0_reg    <= 8'd0;
      x1_reg    <= 8'd0;
      x2_reg    <= 8'd0;
      x3_reg    <= 8'd0;
      sum_reg   <= 10'd0;
      div_start <= 1'b0;
      out_reg   <= 8'd0;
      valid_reg <= 1'b0;
      done_reg  <= 1'b0;
    end else begin
      div_start <= 1'b0;
      valid_reg <= 1'b0;

      case (state)
        S_IDLE: begin
          done_reg <= 1'b0;
          out_reg  <= 8'd0;
          idx      <= 2'd0;
          if (ui_in[7]) state <= S_LOAD;
        end

        S_LOAD: begin
          case (idx)
            2'd0:    x0_reg <= ui_in;
            2'd1:    x1_reg <= ui_in;
            2'd2:    x2_reg <= ui_in;
            default: x3_reg <= ui_in;
          endcase
          idx <= idx + 2'd1;
          if (idx == 2'd3) state <= S_SUM;
        end

        S_SUM: begin
          sum_reg <= sum_w;   // >= 255: the max lane always contributes e^0
          idx     <= 2'd0;
          state   <= S_DIV;
        end

        S_DIV: begin
          div_start <= 1'b1;
          state     <= S_DIV_WAIT;
        end

        S_DIV_WAIT: begin
          if (div_done_w) begin
            out_reg   <= q_w;
            valid_reg <= 1'b1;
            idx       <= idx + 2'd1;
            state     <= (idx == 2'd3) ? S_DONE : S_DIV;
          end
        end

        default: begin  // S_DONE: hold until reset, as before
          done_reg <= 1'b1;
          out_reg  <= 8'h80;
          state    <= S_DONE;
        end
      endcase
    end
  end

  assign uo_out  = out_reg;
  assign uio_out = {6'b000000, valid_reg, done_reg};
  assign uio_oe  = 8'b00000011;

  wire _unused = &{ena, uio_in, 1'b0};

endmodule
