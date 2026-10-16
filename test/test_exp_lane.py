import math

import cocotb
from cocotb.triggers import Timer

# Segment table of the RTL: (first code, (a, c, sign), offset) -> y = (n>>a) +/- (n>>c) + b
SEGS = [[-1665, [7, 10, 1], 15], [-903, [4, 6, -1], 49], [-654, [3, 7, -1], 95], [-453, [2, 5, -1], 141], [-337, [2, 4, 1], 174], [-257, [1, 4, -1], 205], [-159, [1, 3, 1], 236], [-76, [0, 3, -1], 254]]


def model(n: int) -> int:
    if n < SEGS[0][0]:
        return 0
    for x0, (a, c, sg), b in reversed(SEGS):
        if n >= x0:
            v = (n >> a) + (sg * (n >> c) if sg else 0) + b
            return max(0, min(255, v))
    return 0


@cocotb.test()
async def test_exp_lane_exhaustive(dut):
    """Every input in [-8.0, 0] matches the bit-level model and stays within
    1.84 LSB of 255 * e^x."""
    worst = 0.0
    for n in range(-2048, 1):
        dut.n_i.value = n & 0xFFF
        await Timer(1, unit="ns")
        got = int(dut.p_o.value)
        assert got == model(n), f"n={n}: rtl {got} != model {model(n)}"
        worst = max(worst, abs(got - 255 * math.exp(n / 256)))
    dut._log.info(f"worst error vs 255*e^x: {worst:.2f} LSB")
    assert worst <= 1.85


@cocotb.test()
async def test_exp_lane_monotonic(dut):
    prev = -1
    for n in range(-2048, 1):
        dut.n_i.value = n & 0xFFF
        await Timer(1, unit="ns")
        got = int(dut.p_o.value)
        assert got >= prev, f"not monotonic at n={n}: {prev} -> {got}"
        prev = got
