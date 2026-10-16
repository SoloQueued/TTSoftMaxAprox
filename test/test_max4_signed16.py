import random

import cocotb
from cocotb.triggers import Timer


def to_s16(value: int) -> int:
    value &= 0xFFFF
    return value - 65536 if value & 0x8000 else value


@cocotb.test()
async def test_max4_signed16(dut):
    rng = random.Random(4)
    vectors = [(-5, -2, -9, -2), (0, 0, 0, 0), (32767, -32768, 3, 4), (-32768, -32767, -32766, -32765)]
    vectors += [tuple(rng.randint(-32768, 32767) for _ in range(4)) for _ in range(200)]
    for a, b, c, d in vectors:
        dut.a_i.value = a & 0xFFFF
        dut.b_i.value = b & 0xFFFF
        dut.c_i.value = c & 0xFFFF
        dut.d_i.value = d & 0xFFFF
        await Timer(1, unit="ns")
        got = to_s16(int(dut.max_val_o.value))
        assert got == max(a, b, c, d), f"{(a, b, c, d)}: expected {max(a, b, c, d)}, got {got}"
