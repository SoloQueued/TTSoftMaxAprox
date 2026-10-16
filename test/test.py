# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import math
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

ONE = 256  # inputs are signed Q8.8


def to_code(v: float) -> int:
    return max(-32768, min(32767, int(round(v * ONE))))


async def reset_dut(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 4)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_softmax_transaction(dut, codes):
    # Start pulse in IDLE, then 8 bytes: high byte then low byte for each input
    dut.ui_in.value = 0x80
    await RisingEdge(dut.clk)
    for c in codes:
        c &= 0xFFFF
        dut.ui_in.value = c >> 8
        await RisingEdge(dut.clk)
        dut.ui_in.value = c & 0xFF
        await RisingEdge(dut.clk)
    dut.ui_in.value = 0
    outputs = []
    done_seen = False
    for _ in range(150):
        await RisingEdge(dut.clk)
        if int(dut.uio_out.value) & 0x2:
            outputs.append(int(dut.uo_out.value))
        if int(dut.uio_out.value) & 0x1:
            done_seen = True
            break
    return outputs, done_seen


def softmax_ref(codes):
    v = [c / ONE for c in codes]
    m = max(v)
    e = [math.exp(x - m) for x in v]
    s = sum(e)
    return [x / s for x in e]


def l1_err(outputs, ref):
    # total absolute error over the 4 probabilities (0 = exact, 2 = worst)
    return sum(abs(o / 256 - r) for o, r in zip(outputs, ref))


async def check_vector(dut, codes, tol=0.04):
    await reset_dut(dut)
    outputs, done_seen = await run_softmax_transaction(dut, codes)
    assert done_seen and len(outputs) == 4, f"{codes}: protocol failure, got {outputs}"
    for o in outputs:
        assert 0 <= o <= 255
    ref = softmax_ref(codes)
    err = l1_err(outputs, ref)
    assert err <= tol, f"{[c / ONE for c in codes]}: got {outputs}, ref {[round(r * 256) for r in ref]}, L1 {err:.3f}"
    top = max(range(4), key=lambda i: codes[i])
    assert outputs[top] == max(outputs), f"{codes}: largest input did not get the largest output {outputs}"
    return err, outputs, ref


@cocotb.test()
async def test_project(dut):
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())

    directed = [
        [1, 2, 3, 4], [0, 0, 0, 0], [4, 3, 2, 1], [0.5, 0.25, 0, -0.25],
        [-8, -6, -4, -2], [127.996, 127.996, 127.996, 127.996], [-128, -128, -128, -128],
        [127.996, -128, 0, 64], [50, 50, 50, 51], [100, 100, 50, 50], [10, 10.5, 11, 11.5],
        [20, 20, 20, 21], [30, 30.75, 30, 30.75], [-50, -40, 40, 50], [0, 0, 0, 100],
        [0, 0, 0, 1], [0, 0, 0, 0.0039], [1.1, 2.2, 0.3, -0.4], [-0.1, -0.2, -0.3, -0.4],
        [3.14159, 2.71828, 1.41421, 1.73205], [42, 42, 43, 41], [5, -10, 15, -5],
        [-30, -20, -10, 0], [99, 100, 101, 102], [0.01, 0.02, 0.03, 0.04],
        [-6.5, 0, -6.5, -6.5], [-5.5, -5, -4.5, -4],
    ]
    errs = []
    for vec in directed:
        codes = [to_code(v) for v in vec]
        err, out, ref = await check_vector(dut, codes)
        errs.append(err)
        dut._log.info(f"{vec} -> {out} (ref {[round(r * 256) for r in ref]}), L1 {err:.4f}")
    avg = sum(errs) / len(errs)
    dut._log.info(f"Directed: {len(errs)} vectors, L1 avg {avg:.4f}, max {max(errs):.4f}")
    assert avg <= 0.015, f"Average L1 error too high: {avg:.4f}"


@cocotb.test()
async def test_random_vectors(dut):
    """500 random input sets: half spread over the full range, half clustered
    within +/-2.0, where softmax is soft and precision matters most."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    rng = random.Random(2026)
    errs = []
    for i in range(500):
        if i % 2:
            codes = [rng.randint(-32768, 32767) for _ in range(4)]
        else:
            base = rng.randint(-30000, 30000)
            codes = [max(-32768, min(32767, base + rng.randint(-512, 512))) for _ in range(4)]
        err, _, _ = await check_vector(dut, codes)
        errs.append(err)
    avg = sum(errs) / len(errs)
    dut._log.info(f"Random sweep: 500 vectors, L1 avg {avg:.4f}, max {max(errs):.4f}")
    assert avg <= 0.015, f"Average L1 error too high: {avg:.4f}"
