import os

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, FallingEdge

N = int(os.environ.get("N", "4"))
PIPE = int(os.environ.get("PIPE_STAGES", "0"))
WEIGHT_SETS = int(os.environ.get("WEIGHT_SETS", "25"))
ROWS_PER_SET = int(os.environ.get("ROWS_PER_SET", "400"))


def pack(values, width):
    word = 0
    mask = (1 << width) - 1
    for idx, v in enumerate(values):
        word |= (int(v) & mask) << (idx * width)
    return word


def unpack_signed(word, count, width):
    out = []
    mask = (1 << width) - 1
    for idx in range(count):
        v = (word >> (idx * width)) & mask
        if v >> (width - 1):
            v -= 1 << width
        out.append(v)
    return out


@cocotb.test()
async def matmul_random(dut):
    rng = np.random.default_rng(2026)
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    dut.w_load.value = 0
    dut.w_flat.value = 0
    dut.a_row.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1

    total = 0
    mismatches = 0
    for _ in range(WEIGHT_SETS):
        W = rng.integers(-128, 128, size=(N, N), dtype=np.int64)
        A = rng.integers(-128, 128, size=(ROWS_PER_SET, N), dtype=np.int64)
        golden = A @ W

        await FallingEdge(dut.clk)
        dut.w_flat.value = pack(W.flatten(), 8)
        dut.w_load.value = 1
        await FallingEdge(dut.clk)
        dut.w_load.value = 0

        cycles = ROWS_PER_SET + 2 * N + PIPE + 2
        samples = []
        for c in range(cycles):
            lanes = []
            for i in range(N):
                k = c - i
                lanes.append(A[k][i] if 0 <= k < ROWS_PER_SET else 0)
            dut.a_row.value = pack(lanes, 8)
            await RisingEdge(dut.clk)
            await ReadOnly()
            samples.append(unpack_signed(int(dut.c_col.value), N, 32))
            await FallingEdge(dut.clk)

        for k in range(ROWS_PER_SET):
            for j in range(N):
                got = samples[k + N - 1 + j + PIPE][j]
                if got != golden[k][j]:
                    mismatches += 1
            total += 1

    dut._log.info("N=%d PIPE=%d vectors=%d mismatches=%d", N, PIPE, total, mismatches)
    assert mismatches == 0, f"{mismatches} mismatches"
