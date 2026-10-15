import csv
import re
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
RESULTS = ROOT / "results"
FLOP_OVERHEAD_NS = 0.5

AREA_RE = re.compile(r"Chip area for module .*?: ([0-9.]+)")
DELAY_RE = re.compile(r"Delay =\s+([0-9.]+) ps")
CELLS_RE = re.compile(r"Number of cells:\s+(\d+)")
DFF_RE = re.compile(r"^\s+sky130_fd_sc_hd__df\w+\s+(\d+)", re.MULTILINE)


def synth(n, pipe):
    BUILD.mkdir(exist_ok=True)
    template = (ROOT / "flow" / "synth.ys.tmpl").read_text()
    script = template.replace("@N@", str(n)).replace("@PIPE@", str(pipe))
    ys = BUILD / f"synth_n{n}_p{pipe}.ys"
    log = BUILD / f"synth_n{n}_p{pipe}.log"
    ys.write_text(script)
    subprocess.run(["yosys", "-q", "-l", str(log), str(ys)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    text = log.read_text()
    area_um2 = float(AREA_RE.findall(text)[-1])
    delay_ns = float(DELAY_RE.findall(text)[-1]) / 1000.0
    cells = int(CELLS_RE.findall(text)[-1])
    flops = sum(int(x) for x in DFF_RE.findall(text))
    fmax_mhz = 1000.0 / (delay_ns + FLOP_OVERHEAD_NS)
    return {
        "N": n,
        "PIPE_STAGES": pipe,
        "area_um2": round(area_um2, 1),
        "area_mm2": round(area_um2 / 1e6, 4),
        "crit_path_ns": round(delay_ns, 3),
        "fmax_est_mhz": round(fmax_mhz, 1),
        "cells": cells,
        "flops": flops,
        "macs": n * n,
        "peak_gops_est": round(2 * n * n * fmax_mhz / 1000.0, 2),
    }


def main():
    RESULTS.mkdir(exist_ok=True)
    rows = []
    for n in (4, 8):
        for pipe in (0, 1):
            row = synth(n, pipe)
            rows.append(row)
            print(row)

    with open(RESULTS / "ppa.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "| N | PIPE | Area (mm^2) | Cells | Flops | Critical path (ns) | Est. fmax (MHz) | Est. peak GOPS |",
        "|---|------|-------------|-------|-------|--------------------|-----------------|----------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['N']} | {r['PIPE_STAGES']} | {r['area_mm2']} | {r['cells']} | {r['flops']} | "
            f"{r['crit_path_ns']} | {r['fmax_est_mhz']} | {r['peak_gops_est']} |"
        )
    (RESULTS / "ppa.md").write_text("\n".join(lines) + "\n")

    fig, ax = plt.subplots(figsize=(6, 4))
    for pipe, marker in ((0, "o"), (1, "s")):
        pts = [r for r in rows if r["PIPE_STAGES"] == pipe]
        ax.scatter([r["area_mm2"] for r in pts], [r["fmax_est_mhz"] for r in pts], marker=marker, s=60,
                   label=f"PIPE_STAGES={pipe}")
        for r in pts:
            ax.annotate(f"N={r['N']}", (r["area_mm2"], r["fmax_est_mhz"]), textcoords="offset points",
                        xytext=(6, 4), fontsize=8)
    ax.set_xlabel("Area (mm^2)")
    ax.set_ylabel("Estimated fmax (MHz)")
    ax.set_title("Systolic array PPA, Sky130 HD, TT corner (pre-layout)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "ppa_fmax_vs_area.png", dpi=150)


if __name__ == "__main__":
    main()
