"""Disc-level romdiff: every sector that differs between two disc images must belong to an allowed file, and keep its
sync, header and subheader (only user data, EDC and ECC may change). The skill's romdiff.py checks byte by byte in
Python, far too slow for a 650 MB image, so this compares whole sectors with numpy.

usage: discdiff.py ORIG.bin NEW.bin ALLOWED.txt    (one disc path per line, `#` comments); exit 1 on any stray sector
Library: check(orig, new, allowed) -> (errors, {path: changed sectors})"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disc

CHUNK = 4096  # sectors per read


def owners(d):
    """{lba: path} for every sector a file covers."""
    out = {}
    for p, e in d.files.items():
        for i in range(max(1, -(-e.size // 2048))):
            out[e.lba + i] = p
    return out


def changed(orig, new):
    """Sorted LBAs whose 2,352 raw bytes differ."""
    a, b = np.memmap(orig, np.uint8, "r"), np.memmap(new, np.uint8, "r")
    assert len(a) == len(b) and len(a) % disc.SECTOR == 0, "images differ in size"
    out = []
    n = len(a) // disc.SECTOR
    for s in range(0, n, CHUNK):
        k = min(CHUNK, n - s)
        x = a[s * disc.SECTOR:(s + k) * disc.SECTOR].reshape(k, disc.SECTOR)
        y = b[s * disc.SECTOR:(s + k) * disc.SECTOR].reshape(k, disc.SECTOR)
        out += (np.flatnonzero((x != y).any(axis=1)) + s).tolist()
    return out


def check(orig, new, allowed):
    d = disc.Disc(str(orig))
    own = owners(d)
    errs, per = [], {}
    a, b = np.memmap(orig, np.uint8, "r"), np.memmap(new, np.uint8, "r")
    for lba in changed(orig, new):
        p = own.get(lba)
        if p not in allowed:
            errs.append(f"sector {lba}: belongs to {p or 'no file'}, not allowed")
            continue
        o = lba * disc.SECTOR
        if (a[o:o + disc.USER] != b[o:o + disc.USER]).any():
            errs.append(f"sector {lba} ({p}): sync/header/subheader changed")
        per[p] = per.get(p, 0) + 1
    return errs, per


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    allowed = {ln.split("#")[0].strip() for ln in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines()} - {""}
    errs, per = check(sys.argv[1], sys.argv[2], allowed)
    print(*errs[:50], sep="\n")
    print(f"{sum(per.values())} sectors changed in {len(per)} allowed files; {len(errs)} errors")
    sys.exit(1 if errs else 0)
