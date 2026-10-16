# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
import math
import random


async def reset_dut(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 8)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_softmax_transaction(dut, inputs):
    # Start pulse in IDLE
    dut.ui_in.value = 0x80
    await RisingEdge(dut.clk)

    # 4 serialized inputs
    for value in inputs:
        dut.ui_in.value = value & 0xFF
        await RisingEdge(dut.clk)

    dut.ui_in.value = 0

    outputs = []
    done_seen = False
    for cyc in range(120):
        await RisingEdge(dut.clk)
        ser_valid = int(dut.uio_out.value) & 0x2
        done_flag = int(dut.uio_out.value) & 0x1

        if ser_valid:
            outputs.append(int(dut.uo_out.value))
        if done_flag:
            done_seen = True
            break

    return outputs, done_seen


def softmax_ref_u8(inputs):
    m = max(inputs)
    exps = [math.exp(x - m) for x in inputs]
    s = sum(exps)
    probs = [e / s for e in exps]
    return [int(round(p * 255.0)) for p in probs]


def l1_norm_err_u8(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / 255.0


@cocotb.test()
async def test_project(dut):
    dut._log.info("="*70)
    dut._log.info("COMPREHENSIVE SOFTMAX TESTBENCH - 27 directed test vectors")
    dut._log.info("="*70)

    # 10 MHz clock
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Comprehensive test vectors
    test_vectors = [
        # Basic cases (original)
        [10, 20, 30, 40],        # Clear winner
        [0, 0, 0, 0],            # All equal
        [40, 10, 0, -5],         # Large spread
        [-8, -6, -4, -2],        # Negative range
        
        # Edge cases
        [127, 127, 127, 127],    # All max positive
        [-128, -128, -128, -128],# All min negative
        [127, -128, 0, 64],      # Full range mix
        
        # Monotonicity/ordering tests
        [1, 2, 3, 4],            # Strictly increasing
        [4, 3, 2, 1],            # Strictly decreasing
        [50, 50, 50, 51],        # Almost equal with slight winner
        [100, 100, 50, 50],      # Two pairs
        
        # Small differences (differentiation test)
        [10, 11, 12, 13],        # 1 unit steps
        [20, 20, 20, 21],        # One different by 1
        [30, 31, 30, 31],        # Alternating
        
        # Large spread tests
        [-50, -40, 40, 50],      # Large neg to large pos
        [100, 0, 0, 0],          # One dominant
        [0, 0, 0, 100],          # Last one dominant
        
        # Boundary conditions
        [-8, -8, -8, -8],        # Lower negative bound
        [50, 50, 50, 50],        # High equal
        [0, 0, 0, 1],            # Minimal difference at boundary
        
        # Random-like patterns
        [7, 13, 21, 34],         # Fibonacci-like
        [15, 25, 8, 32],         # Random mix
        [42, 42, 43, 41],        # Clustering
        [5, -10, 15, -5],        # Mixed signs
        [-30, -20, -10, 0],      # Negative to zero
        [10, 10, 10, 10],        # Perfect equal (repeat)
        [99, 100, 101, 102],     # Near max boundary
    ]

    nonflat_cases = 0
    errs = []
    argmax_errors = 0
    passed_cases = 0
    failed_cases = 0

    for idx, vec in enumerate(test_vectors, start=1):
        dut._log.info(f"\n[Case {idx:02d}] Testing: {vec}")
        await reset_dut(dut)

        outputs, done_seen = await run_softmax_transaction(dut, vec)
        ref = softmax_ref_u8(vec)

        # Basic assertions
        try:
            assert len(outputs) == 4, f"Expected 4 outputs, got {len(outputs)}"
            assert done_seen, f"Done flag not observed"
            
            for lane, value in enumerate(outputs, start=1):
                assert 0 <= value <= 255, f"Output {lane} out of range: {value}"
            
            spread = max(outputs) - min(outputs)
            if spread > 0:
                nonflat_cases += 1
            
            # Argmax check
            if len(set(vec)) == len(vec) and spread >= 4:
                got_argmax = max(range(4), key=lambda i: outputs[i])
                ref_argmax = max(range(4), key=lambda i: vec[i])
                if got_argmax != ref_argmax:
                    argmax_errors += 1
                    dut._log.warning(f"  Argmax mismatch: got {got_argmax}, expected {ref_argmax}")
                else:
                    dut._log.info(f"  ✓ Argmax correct: {ref_argmax}")
            
            # L1 error check (relaxed tolerance for minimal design)
            err = l1_norm_err_u8(outputs, ref)
            errs.append(err)
            
            # Tolerance: total absolute error across the 4 outputs, as a
            # fraction of full scale (0 = exact, 2 = completely wrong).
            assert err <= 0.05, f"L1 error too high: {err:.3f}"
            
            dut._log.info(f"  Output:  {outputs}")
            dut._log.info(f"  Ref:     {ref}")
            dut._log.info(f"  L1 err:  {err:.3f}")
            passed_cases += 1
            
        except AssertionError as e:
            dut._log.error(f"  ✗ FAILED: {str(e)}")
            failed_cases += 1
            raise

    # Summary statistics
    dut._log.info("\n" + "="*70)
    dut._log.info("TEST SUMMARY")
    dut._log.info("="*70)
    dut._log.info(f"Total cases:        {len(test_vectors)}")
    dut._log.info(f"Passed:             {passed_cases}")
    dut._log.info(f"Failed:             {failed_cases}")
    dut._log.info(f"Non-flat outputs:   {nonflat_cases}")
    dut._log.info(f"Argmax errors:      {argmax_errors}")
    
    if errs:
        avg_err = sum(errs) / len(errs)
        max_err = max(errs)
        min_err = min(errs)
        dut._log.info(f"L1 error - Min:     {min_err:.3f}")
        dut._log.info(f"L1 error - Max:     {max_err:.3f}")
        dut._log.info(f"L1 error - Avg:     {avg_err:.3f}")
    
    dut._log.info("="*70)
    
    # Final assertions
    assert failed_cases == 0, f"{failed_cases} test cases failed"
    assert nonflat_cases >= 10, f"Expected at least 10 non-flat outputs, got {nonflat_cases}"
    if len(errs) > 0:
        avg_err = sum(errs) / len(errs)
        assert avg_err <= 0.02, f"Average L1 error too high: {avg_err:.3f}"
    assert argmax_errors == 0, f"{argmax_errors} argmax errors"
    
    dut._log.info("\n✓ ALL TESTS PASSED\n")

    # Guardrail against completely degenerate behavior.
    assert nonflat_cases >= 1, "All test cases produced flat outputs; expected at least one non-flat response"
    avg_err = sum(errs) / len(errs)
    assert avg_err <= 0.02, f"Average L1 error too high: {avg_err:.3f}"


@cocotb.test()
async def test_random_vectors(dut):
    """500 random input sets, each checked against floating-point softmax."""
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())
    rng = random.Random(2026)
    errs = []
    for _ in range(500):
        # Mix wide-range inputs with tightly clustered ones (where softmax is
        # most sensitive), since clustered inputs exercise every exp value.
        if rng.random() < 0.5:
            vec = [rng.randint(-128, 127) for _ in range(4)]
        else:
            base = rng.randint(-120, 120)
            vec = [max(-128, min(127, base + rng.randint(-7, 7))) for _ in range(4)]
        await reset_dut(dut)
        outputs, done_seen = await run_softmax_transaction(dut, vec)
        assert done_seen and len(outputs) == 4, f"{vec}: protocol failure {outputs}"
        ref = softmax_ref_u8(vec)
        err = l1_norm_err_u8(outputs, ref)
        errs.append(err)
        assert err <= 0.05, f"{vec}: got {outputs}, ref {ref}, L1 {err:.3f}"
        # Largest input must get the largest (or tied-largest) output.
        top = max(range(4), key=lambda i: vec[i])
        assert outputs[top] == max(outputs), f"{vec}: argmax wrong, got {outputs}"
    dut._log.info(f"Random sweep: 500 vectors, L1 avg {sum(errs)/len(errs):.4f}, max {max(errs):.4f}")
