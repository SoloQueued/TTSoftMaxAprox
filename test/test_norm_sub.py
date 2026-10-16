import random

import cocotb
from cocotb.triggers import Timer


def to_s12(value: int) -> int:
    value &= 0xFFF
    return value - 4096 if value & 0x800 else value


@cocotb.test()
async def test_norm_sub(dut):
    """n = x - max, clamped at -8.0 (-2048) so large gaps cannot wrap."""
    rng = random.Random(5)
    cases = [(0, 0), (-1, 0), (-2048, 0), (-2049, 0), (-32768, 32767), (100, 100), (32767, 32767)]
    for _ in range(300):
        m = rng.randint(-32768, 32767)
        cases.append((rng.randint(-32768, m), m))
    for x, m in cases:
        dut.x_i.value = x & 0xFFFF
        dut.max_i.value = m & 0xFFFF
        await Timer(1, unit="ns")
        got = to_s12(int(dut.n_o.value))
        assert got == max(-2048, x - m), f"x={x} max={m}: expected {max(-2048, x - m)}, got {got}"
