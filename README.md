# softmaxAprox(Tiny Tapeout)

LUT-less 4-input softmax accelerator in Verilog for the Tiny Tapeout Sky130 template, for signed Q8.8 (16-bit, 1/256 step) inputs.

## Design summary

This design accepts 4 signed Q8.8 inputs over `ui_in` (two bytes each, high byte first), computes softmax, and returns 4 serialized 8-bit outputs on `uo_out`. Each output is `floor(256 * p_i / sum(p))`, clamped to 255, where `p_i` approximates `255 * e^(x_i - max)`.

There are no lookup tables and no multipliers: the exponential is a shift-only piecewise-linear curve, and normalization is a restoring divider. Because the output pins release one byte per clock, one exponential unit and one divider are time-shared across the four lanes.

Pipeline:

1. `max4_signed16`: signed max of the 4 inputs.
2. `norm_sub`: `n = x - max` for the current lane, saturating at -8.0.
3. `exp_lane`: 8-segment PWL of `255 * e^n`; every slope is one or two powers of two (shifts and adds only), worst-case error 1.84 LSB.
4. Sum: the 4 lanes are accumulated over 4 cycles through the same `exp_lane`.
5. `norm_div`: shared restoring divider computes `min(255, floor(p_i * 256 / sum))` one bit per clock; each result goes straight to `uo_out`.

Top module: `tt_um_nonlut_softmax`

## Interface behavior

- `ui_in[7] = 1` in IDLE starts a transaction.
- Next 8 clock cycles: x0 high byte, x0 low byte, x1 high, x1 low, ... x3 low on `ui_in`.
- `uio_out[1]` pulses for one cycle when each output byte is present on `uo_out` (one byte every 11 cycles; done at cycle 58).
- `uio_out[0]` indicates done for the transaction.

## Files

- RTL: [src](src)
- Tiny Tapeout project metadata: [info.yaml](info.yaml)
- Datasheet markdown source: [docs/info.md](docs/info.md)
- Testbench and cocotb tests: [test](test)

## Testing

From `test/`:

```sh
make -B
```

This runs the self-checking cocotb integration tests (`test/test.py`): 27 directed vectors plus 500 random ones (half full-range, half clustered within +/-2.0), each compared against a floating-point softmax (L1 error <= 0.04 per vector, average <= 0.015, no argmax errors). It produces `results.xml` + waveform output.

Selected module tests:

```sh
make -B test-max4
make -B test-norm-sub
make -B test-exp-lane
make -B test-norm-div
make test-all        # all of the above
```

## Tiny Tapeout

- Template reference: https://github.com/TinyTapeout/ttsky-verilog-template
- Program info: https://tinytapeout.com/

