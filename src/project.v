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

  // v3: LUT-less softmax for four signed Q8.8 inputs.
  // max -> x - max (saturating) -> shift-only PWL e^x -> sum -> shared divider.
  // The output pins only release one byte per clock, so one exp lane and one
  // divider are time-shared across the four lanes instead of duplicated.
  localparam S_IDLE     = 3'd0;
  localparam S_LOAD     = 3'd1;
  localparam S_SUM      = 3'd2;
  localparam S_DIV      = 3'd3;
  localparam S_DIV_WAIT = 3'd4;
  localparam S_DONE     = 3'd5;

  reg [2:0]  state;
  reg [2:0]  byte_idx;  // 8 input bytes: x0 hi, x0 lo, x1 hi, ... x3 lo
  reg [1:0]  lane;      // lane being summed or normalised

  reg [15:0] x0_reg;
  reg [15:0] x1_reg;
  reg [15:0] x2_reg;
  reg [15:0] x3_reg;

  reg [9:0]  sum_reg;   // up to 4 * 255

  reg        div_start;
  reg [7:0]  out_reg;
  reg        valid_reg;
  reg        done_reg;

  wire [15:0] max_val_w;
  reg  [15:0] x_sel;
  wire [11:0] n_w;
  wire [7:0]  p_w;
  wire [7:0]  q_w;
  wire        div_done_w;

  max4_signed16 u_max4 (
      .a_i(x0_reg),
      .b_i(x1_reg),
      .c_i(x2_reg),
      .d_i(x3_reg),
      .max_val_o(max_val_w)
  );

  always @(*) begin
    case (lane)
      2'd0:    x_sel = x0_reg;
      2'd1:    x_sel = x1_reg;
      2'd2:    x_sel = x2_reg;
      default: x_sel = x3_reg;
    endcase
  end

  norm_sub u_norm_sub (
      .x_i(x_sel),
      .max_i(max_val_w),
      .n_o(n_w)
  );

  exp_lane u_exp (
      .n_i(n_w),
      .p_o(p_w)
  );

  norm_div u_div (
      .clk(clk),
      .rst_n(rst_n),
      .start(div_start),
      .p_i(p_w),
      .sum_i(sum_reg),
      .q_o(q_w),
      .done(div_done_w)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state     <= S_IDLE;
      byte_idx  <= 3'd0;
      lane      <= 2'd0;
      x0_reg    <= 16'd0;
      x1_reg    <= 16'd0;
      x2_reg    <= 16'd0;
      x3_reg    <= 16'd0;
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
          byte_idx <= 3'd0;
          if (ui_in[7]) state <= S_LOAD;
        end

        S_LOAD: begin  // high byte first, then low byte, for each input
          case (byte_idx)
            3'd0: x0_reg[15:8] <= ui_in;
            3'd1: x0_reg[7:0]  <= ui_in;
            3'd2: x1_reg[15:8] <= ui_in;
            3'd3: x1_reg[7:0]  <= ui_in;
            3'd4: x2_reg[15:8] <= ui_in;
            3'd5: x2_reg[7:0]  <= ui_in;
            3'd6: x3_reg[15:8] <= ui_in;
            default: x3_reg[7:0] <= ui_in;
          endcase
          byte_idx <= byte_idx + 3'd1;
          if (byte_idx == 3'd7) begin
            lane    <= 2'd0;
            sum_reg <= 10'd0;
            state   <= S_SUM;
          end
        end

        S_SUM: begin  // one lane per cycle through the shared exp unit
          sum_reg <= sum_reg + {2'b00, p_w};
          lane    <= lane + 2'd1;
          if (lane == 2'd3) state <= S_DIV;  // lane wraps to 0
        end

        S_DIV: begin
          div_start <= 1'b1;   // divider latches p_w for this lane next cycle
          state     <= S_DIV_WAIT;
        end

        S_DIV_WAIT: begin
          if (div_done_w) begin
            out_reg   <= q_w;
            valid_reg <= 1'b1;
            lane      <= lane + 2'd1;
            state     <= (lane == 2'd3) ? S_DONE : S_DIV;
          end
        end

        default: begin  // S_DONE: hold until reset
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
