import os
import sys
from pathlib import Path

from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parent.parent


def run(n, pipe):
    os.environ["N"] = str(n)
    os.environ["PIPE_STAGES"] = str(pipe)
    runner = get_runner("icarus")
    build_dir = ROOT / "build" / f"sim_n{n}_p{pipe}"
    runner.build(
        sources=[ROOT / "rtl" / "pe.v", ROOT / "rtl" / "systolic_array.v"],
        hdl_toplevel="systolic_array",
        parameters={"N": n, "PIPE_STAGES": pipe},
        build_dir=build_dir,
        always=True,
    )
    runner.test(
        hdl_toplevel="systolic_array",
        test_module="test_systolic",
        test_dir=ROOT / "tb",
        build_dir=build_dir,
    )


if __name__ == "__main__":
    configs = [(4, 0), (4, 1), (8, 0), (8, 1)]
    if len(sys.argv) == 3:
        configs = [(int(sys.argv[1]), int(sys.argv[2]))]
    for n, pipe in configs:
        run(n, pipe)
