# softmaxAprox(Tiny Tapeout)

4-input softmax accelerator implemented in Verilog for the Tiny Tapeout Sky130 template.

## Design summary

This design accepts 4 signed 8-bit inputs over `ui_in` (serially), computes softmax, and returns 4 serialized 8-bit outputs on `uo_out` (each output is `floor(256 * p_i / sum(p))`, clamped to 255, within a few LSB of a floating-point softmax).

Pipeline stages:

1. `max4_signed8`: signed max of the 4 inputs.
2. `norm_sub4`: subtract the max from each lane, saturating at -128 so extreme inputs cannot wrap.
3. `exp_lane` x4: `round(255 * e^n)` for integer `n = x - max`; only 7 values are non-zero, so a 7-way select is exact.
4. `sum4_tree`: sum the 4 exponential lanes (10 bits).
5. `norm_div`: one shared restoring divider computes `min(255, floor(p_i * 256 / sum))` one bit per clock, and each lane's result goes straight to `uo_out`.

Top module: `tt_um_nonlut_softmax`

## Interface behavior

- `ui_in[7] = 1` in IDLE starts a transaction.
- Next 4 clock cycles: present 4 signed input bytes on `ui_in`.
- `uio_out[1]` pulses for one cycle when each output byte is present on `uo_out` (one byte every 11 cycles; done at cycle 50).
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

This runs the self-checking cocotb integration tests (`test/test.py`): 27 directed vectors plus 500 random ones, each compared against a floating-point softmax (L1 error <= 0.05, average <= 0.02, no argmax errors). It produces `results.xml` + waveform output.

Selected module tests:

```sh
make -B test-max4
make -B test-norm-sub4
make -B test-exp-lane
make -B test-sum4-tree
make -B test-norm-div
make test-all        # all of the above
```

## Tiny Tapeout

- Template reference: https://github.com/TinyTapeout/ttsky-verilog-template
- Program info: https://tinytapeout.com/

For assignment submission, provide the public repository URL and the full commit SHA you want graded.
