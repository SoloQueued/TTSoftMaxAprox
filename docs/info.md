## How it works

This project is a **LUT-less 4-input softmax accelerator** implemented in Verilog for the Tiny Tapeout Sky130 template. It takes **four signed Q8.8 inputs** (16 bits each: 8 integer bits, 8 fractional bits, so steps of 1/256) and returns **four 8-bit probabilities**, one at a time.

There are no lookup tables and no multipliers anywhere in the datapath: the exponential is a piecewise-linear curve whose slopes are only shifts, and normalization is a restoring divider. On the test suite the outputs are within about 0.6% (average L1) of a floating-point softmax.

Top module: `tt_um_nonlut_softmax` (see `src/project.v`).

---

### Transaction / interface behavior

- **Start**: assert `ui_in[7]=1` for one cycle while the design is idle.
- **Load inputs**: on the next 8 cycles, drive x0 high byte, x0 low byte, x1 high byte, x1 low byte, ... x3 low byte on `ui_in[7:0]` (two's complement Q8.8).
- **Outputs**: the 4 result bytes appear on `uo_out[7:0]`, lane 0 first, one every 11 cycles.

Status bits:
- `uio_out[1]` = **valid** (one-cycle pulse when a new output byte is on `uo_out`)
- `uio_out[0]` = **done** (transaction complete; held until reset)

A full transaction takes 58 cycles from the start pulse to done (5.8 us at the 10 MHz clock).

---

## Design dataflow (as implemented)

The output pins can only release one byte per clock, so instead of four copies of each block, one subtractor, one exponential unit and one divider are time-shared across the lanes.

### 1) Max (`max4_signed16`)
Finds the maximum of the four signed 16-bit inputs.

### 2) Subtract max (`norm_sub`)
For the current lane, `n = x - max`, the standard numerical-stability step of softmax. `n` is always <= 0; it is computed in 17 bits and clamped at -8.0, since `255 * e^n` rounds to 0 well before that.

### 3) Exponential (`exp_lane`)
An 8-segment piecewise-linear fit of `255 * e^n` over [-6.5, 0]. Each segment is

`y = (n >>> a) +/- (n >>> c) + b`

so every slope is one or two powers of two: shifts and adds only. Breakpoints and offsets were fitted for the smallest worst-case error, which is **1.84 LSB** over all 2,049 possible inputs. For comparison, an exact lookup table for the same input range needs 1,597 entries and synthesizes to more than twice the area.

### 4) Sum
The four exponentials are accumulated over 4 cycles through the same `exp_lane` (10-bit sum).

### 5) Normalization (`norm_div`)
One restoring divider computes `q = min(255, floor(p_i * 256 / sum))`, one quotient bit per clock: double the remainder, subtract the sum if it fits, shift in a 1 or 0. Each lane's exponential is recomputed from the stored inputs as its turn comes, and each quotient goes straight to `uo_out` with a `valid` pulse.

---

## How to test

The project uses a **cocotb-based, self-checking test flow** (Icarus by default) defined under `test/`.

### Run the default end-to-end tests (recommended)

From the `test/` directory:

```sh
make -B
```

This runs `test/test.py`: 27 directed vectors plus 500 random input sets (half spread over the full range, half clustered within +/-2.0, where softmax is soft), each compared against a floating-point softmax. A case fails if its total L1 error exceeds 0.04 (on a 0-2 scale) or if the largest input does not get the largest output; the average must stay under 0.015. Artifacts include `results.xml` and `tb.fst`.

### Module-level unit tests

```sh
make -B test-max4
make -B test-norm-sub
make -B test-exp-lane
make -B test-norm-div
make test-all
```

`test-exp-lane` checks every input against the bit-level segment model and against `255 * e^x`; `test-norm-div` checks the divider against `floor(p * 256 / sum)` on edge cases and 300 random pairs.

---

## AI Usage
Using Perplexity I generated some ideas for the tape-out and narrowed in on the SoftMax, and helped me plan out what modules I needed to make. After making the original modules, Copilot helped me generate tests for the individual modules, as well as helping test the top module once all submodules were tested. 

After compiling, I found the gate count to be far too high, at about 9000 gates. I asked copilot to help me decrease the bitwidths of modules,replace multipliers for shift approximation, switch from the original Newton-Raphson calculation for a LUT in the recprical calculator, and decreasing the exponential linear approximation fidelity from 6 segments to 4 to decrease the gate count. Afterwards, AI was used to edit test parameters to fit the new scope and modify config files for a final gate count of ~1.5k gates.


Finally, AI was used to confirm attributes of the project for the MD. 

In October 2026 I revisited this project with an AI assistant as a validation step. This produced an exact integer softmax for the same 1×1 tile (an exact exponential, a saturating max subtraction and a shared divider), with the tests tightened from an L1 tolerance of 1.5 to 0.05 and a 500-vector random sweep. I set the goals and constraints and reviewed the results. The comparison invalidated the original premise as the exact version is both smaller and far more accurate than the approximation, so the LUT-less approach offered no advantage at this input format.

In October 2026 I continued with an AI assistant to test the original LUT-less idea properly. This produced v3: signed Q8.8 inputs, a shift-only 8-segment PWL exponential (no lookup tables, no multipliers) and the shared divider, with one exponential unit and one divider time-shared across the four lanes. I set the goals and constraints and reviewed the results. Against an exact-table version built in the same frame, the LUT-less exponential is less than half the area (about 2,000 vs 4,560 um2) with at most 1.84 LSB of error, which supports the original premise once the inputs have real fractional precision.

## External hardware

No external hardware is required.