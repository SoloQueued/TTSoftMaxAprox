import math

import cocotb
from cocotb.triggers import Timer


def to_u8(value: int) -> int:
    return value & 0xFF


def model_exp_lane(n: int) -> int:
    # round(255 * e^n) for integer n <= 0; 0 for n <= -7
    return int(round(255 * math.exp(n))) if n <= 0 else 0


@cocotb.test()
async def test_exp_lane_exact(dut):
    # Every reachable input (x - max is in [-128, 0]) matches the exact model
    for n in range(-128, 1):
        dut.x_i.value = to_u8(n)
        await Timer(1, unit="ns")
        got = int(dut.exp_o.value)
        expected = model_exp_lane(n)
        assert got == expected, f"n={n}: expected {expected}, got {got}"


@cocotb.test()
async def test_exp_lane_monotonic(dut):
    prev = -1
    for n in range(-128, 1):
        dut.x_i.value = to_u8(n)
        await Timer(1, unit="ns")
        got = int(dut.exp_o.value)
        assert got >= prev, f"not monotonic at n={n}: {prev} -> {got}"
        prev = got
