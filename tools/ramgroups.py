"""Find state variables: RAM addresses constant within each group of dumps and different between groups.

    python -X utf8 tools/ramgroups.py DIR LABEL=F1,F2.. LABEL=F1-F2 .. [--width 1|2|4] [--max 60] [--all-distinct]

DIR holds ram_<frame>.bin (probes/ramdump.lua). A group is a label and frames (list or inclusive range; frames are
matched to the dumps present). Prints address (0x80xxxxxx) and the value per group, small values first.
"""
import argparse
import glob
import os
import re

import numpy as np


def frames_of(spec, have):
    out = []
    for part in spec.split(","):
        if "-" in part:
            lo, hi = map(int, part.split("-"))
            out += [f for f in have if lo <= f <= hi]
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("groups", nargs="+")
    ap.add_argument("--width", type=int, default=2)
    ap.add_argument("--max", type=int, default=60)
    ap.add_argument("--all-distinct", action="store_true", help="every group's value differs from every other's")
    a = ap.parse_args()
    have = sorted(int(re.search(r"(\d+)", os.path.basename(p)).group(1)) for p in glob.glob(os.path.join(a.dir, "ram_*.bin")))
    dt = {1: "<u1", 2: "<u2", 4: "<u4"}[a.width]
    vals = []
    for g in a.groups:
        label, spec = g.split("=", 1)
        fs = frames_of(spec, have)
        arr = np.stack([np.frombuffer(open(os.path.join(a.dir, f"ram_{f:06d}.bin"), "rb").read(), dtype=dt) for f in fs])
        const = (arr == arr[0]).all(axis=0)
        vals.append((label, arr[0], const))
    ok = np.logical_and.reduce([c for _, _, c in vals])
    if a.all_distinct:
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                ok &= vals[i][1] != vals[j][1]
    else:
        ok &= np.logical_or.reduce([vals[i][1] != vals[0][1] for i in range(1, len(vals))])
    idx = np.nonzero(ok)[0]
    mx = np.max(np.stack([v[1][idx] for v in vals]), axis=0) if len(idx) else []
    order = idx[np.argsort(mx, kind="stable")] if len(idx) else idx
    print(f"{len(idx)} candidates; " + " ".join(v[0] for v in vals))
    for i in order[: a.max]:
        print(f"{0x80000000 + i * a.width:08X} " + " ".join(f"{int(v[1][i]):X}" for v in vals))


if __name__ == "__main__":
    main()
