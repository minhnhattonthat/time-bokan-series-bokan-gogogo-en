"""Find a menu cursor from probe dumps ram_p0.bin..ram_pN.bin taken one key press apart.

    python -X utf8 tools/cursorfind.py DIR [--width 4] [--start 0] [--wrap N]

Prints addresses whose value goes start, start+1, ... (optionally wrapping to 0 after N-1), and addresses that
go up by one each press regardless of start.
"""
import argparse
import glob
import os

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--width", type=int, default=4)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--wrap", type=int, default=0)
    ap.add_argument("--step", type=int, default=1)
    a = ap.parse_args()
    n = len(glob.glob(os.path.join(a.dir, "ram_p*.bin")))
    dt = {1: "<u1", 2: "<u2", 4: "<u4"}[a.width]
    arr = np.stack([np.frombuffer(open(os.path.join(a.dir, f"ram_p{i}.bin"), "rb").read(), dtype=dt)
                    for i in range(n)]).astype(np.int64)
    want = np.array([a.start + a.step * i for i in range(n)])
    if a.wrap:
        want %= a.wrap
    exact = np.nonzero((arr == want[:, None]).all(axis=0))[0]
    print(f"exact {list(want)}: " + " ".join(f"{0x80000000 + i * a.width:08X}" for i in exact[:20]))
    d = np.diff(arr, axis=0)
    rel = np.nonzero((d == a.step).all(axis=0))[0]
    for i in rel[:15]:
        print(f"+{a.step} each: {0x80000000 + i * a.width:08X} " + " ".join(str(v) for v in arr[:, i]))


if __name__ == "__main__":
    main()
