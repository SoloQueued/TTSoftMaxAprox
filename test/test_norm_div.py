import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


def model(p: int, s: int) -> int:
    return min(255, (p * 256) // s)


async def divide(dut, p: int, s: int) -> int:
    dut.p_i.value = p
    dut.sum_i.value = s
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    for _ in range(20):
        await RisingEdge(dut.clk)
        if int(dut.done.value):
            return int(dut.q_o.value)
    raise AssertionError(f"no done for p={p} s={s}")


@cocotb.test()
async def test_norm_div(dut):
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    dut.start.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Edges: p == sum (single winner), all-equal, smallest non-zero, zero lane
    cases = [(255, 255), (255, 1020), (64, 1020), (1, 1020), (0, 255), (255, 256), (94, 349), (13, 255)]
    rng = random.Random(118)
    for _ in range(300):
        s = rng.randint(255, 1020)  # the max lane always contributes 255
        cases.append((rng.randint(0, min(255, s)), s))

    for p, s in cases:
        got = await divide(dut, p, s)
        assert got == model(p, s), f"p={p} s={s}: expected {model(p, s)}, got {got}"
