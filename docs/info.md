## How it works

This project is a **4-input softmax accelerator** implemented in Verilog for the Tiny Tapeout Sky130 template.

It accepts **four signed 8-bit inputs serially** and returns **four 8-bit outputs**, one at a time. Each output is `floor(256 * p_i / sum(p))` (clamped to 255), where `p_i = round(255 * e^(x_i - max))`. On the test suite the result is within about 1% (L1) of a floating-point softmax.

Top module: `tt_um_nonlut_softmax` (see `src/project.v`).

---

### Transaction / interface behavior

A transaction is controlled entirely through `ui_in` (inputs) and `uio_out` (status):

- **Start**: assert `ui_in[7]=1` for one cycle while the design is idle.
- **Load inputs**: on the next 4 cycles, drive one signed 8-bit value per cycle on `ui_in[7:0]`.
- **Outputs**: the 4 output bytes appear on `uo_out[7:0]`, one every 11 cycles, lane 0 first.

Status bits:
- `uio_out[1]` = **valid** (one-cycle pulse when a new output byte is on `uo_out`)
- `uio_out[0]` = **done** (transaction complete; held until reset)

A full transaction takes 50 cycles from the start pulse to done (5 us at the 10 MHz clock).

---

## Design dataflow (as implemented)

### 1) Max + normalization (`max4_signed8`, `norm_sub4`)
- `max4_signed8` finds the maximum of the four signed inputs.
- `norm_sub4` subtracts that maximum from each lane: `n_i = x_i - max(x)`.

This is the standard "numerical stability" trick used in real softmax implementations. The difference can reach -255, which does not fit in 8 bits, so it is computed in 9 bits and saturated at -128 (anything below -6 gives an exponential of 0 anyway).

### 2) Exponential (`exp_lane`)
The inputs are integers, so after subtracting the max, `n_i` is an integer <= 0, and `255 * e^n` rounds to zero for every `n <= -7`. That leaves only seven non-zero results:

| n | 0 | -1 | -2 | -3 | -4 | -5 | -6 | <= -7 |
|---|---|----|----|----|----|----|----|-------|
| `exp_o` | 255 | 94 | 35 | 13 | 5 | 2 | 1 | 0 |

`exp_lane` is a 7-way select, which is exact for every reachable input and smaller than the earlier piecewise-linear approximation.

### 3) Sum (`sum4_tree`)
The four 8-bit exponentials are summed into a 10-bit value. The max lane always contributes 255, so the sum is between 255 and 1020 and never zero.

### 4) Normalization (`norm_div`)
One restoring divider, shared by all four lanes, computes `q = floor(p_i * 256 / sum)` one quotient bit per clock (8 clocks per lane). Because `p_i` is one of the summands, `p_i <= sum` and the running remainder fits in 11 bits; when `p_i == sum` (every other lane is 0) the loop naturally produces 255. Each quotient is driven straight onto `uo_out` with a `valid` pulse, so no separate serializer or output registers are needed.

---

## How to test

The project uses a **cocotb-based, self-checking test flow** (Icarus by default) defined under `test/`.

### Run the default end-to-end tests (recommended)

From the `test/` directory:

```sh
make -B
```

This runs `test/test.py`: the original 27 directed vectors plus 500 random input sets, each compared against a floating-point softmax. A case fails if its total L1 error exceeds 0.05 (on a 0-2 scale) or if the largest input does not get the largest output. Artifacts include `results.xml` (test summary) and `tb.fst` (waveform dump).

### Module-level unit tests

```sh
make -B test-max4
make -B test-norm-sub4
make -B test-exp-lane
make -B test-sum4-tree
make -B test-norm-div
make test-all
```

`test-exp-lane` checks every reachable input against `round(255 * e^n)`; `test-norm-div` checks the divider against `floor(p * 256 / sum)` on edge cases and 300 random pairs.

---

## AI Usage
Using Perplexity I generated some ideas for the tape-out and narrowed in on the SoftMax, and helped me plan out what modules I needed to make. After making the original modules, Copilot helped me generate tests for the individual modules, as well as helping test the top module once all submodules were tested. 

After compiling, I found the gate count to be far too high, at about 9000 gates. I asked copilot to help me decrease the bitwidths of modules,replace multipliers for shift approximation, switch from the original Newton-Raphson calculation for a LUT in the recprical calculator, and decreasing the exponential linear approximation fidelity from 6 segments to 4 to decrease the gate count. Afterwards, AI was used to edit test parameters to fit the new scope and modify config files for a final gate count of ~1.5k gates.


Finally, AI was used to confirm attributes of the project for the MD. 

In October 2026 I revisited this project with an AI assistant as a validation step. This produced an exact integer softmax for the same 1×1 tile (an exact exponential, a saturating max subtraction and a shared divider), with the tests tightened from an L1 tolerance of 1.5 to 0.05 and a 500-vector random sweep. I set the goals and constraints and reviewed the results. The comparison invalidated the original premise as the exact version is both smaller and far more accurate than the approximation, so the LUT-less approach offered no advantage at this input format.

## External hardware

No external hardware is required.