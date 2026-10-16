import cocotb
from cocotb.triggers import Timer


def to_u8(value: int) -> int:
    return value & 0xFF


def to_s8(value: int) -> int:
    value &= 0xFF
    return value - 256 if value & 0x80 else value


@cocotb.test()
async def test_norm_sub4_basic(dut):
    vectors = [
        (10, 8, 6, 4, 10),
        (-1, -2, -3, -4, -1),
        (127, -128, 0, 64, 127),
        (0, 0, 0, 0, 0),
        (-128, -100, 0, 127, 127),
    ]

    for idx, (a, b, c, d, m) in enumerate(vectors, start=1):
        dut.a_i.value = to_u8(a)
        dut.b_i.value = to_u8(b)
        dut.c_i.value = to_u8(c)
        dut.d_i.value = to_u8(d)
        dut.max_i.value = to_u8(m)

        await Timer(1, unit="ns")

        exp_a = max(-128, a - m)  # saturates instead of wrapping
        exp_b = max(-128, b - m)
        exp_c = max(-128, c - m)
        exp_d = max(-128, d - m)

        got_a = to_s8(int(dut.a_o.value))
        got_b = to_s8(int(dut.b_o.value))
        got_c = to_s8(int(dut.c_o.value))
        got_d = to_s8(int(dut.d_o.value))

        assert (got_a, got_b, got_c, got_d) == (exp_a, exp_b, exp_c, exp_d), (
            f"Case {idx}: expected {(exp_a, exp_b, exp_c, exp_d)}, got {(got_a, got_b, got_c, got_d)}"
        )
