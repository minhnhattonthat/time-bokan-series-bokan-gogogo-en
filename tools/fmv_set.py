"""Set the en column of script/fmv rows from a fix list, so review fixes don't hand-edit 18 TSVs.

usage: fmv_set.py FIX.tsv   (lines: movie<TAB>start<TAB>en, e.g. BOGO03<TAB>4.56<TAB>Leave it to us!)
Fails unless every fix line matches exactly one row by movie and start time."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(path):
    fix = {}
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            m, s, t = ln.split("\t")
            assert t.isascii() and t.strip(), t
            assert (m, s) not in fix, (m, s)
            fix[m, s] = t
    done = set()
    for m in sorted({m for m, _ in fix}):
        f = ROOT / "script" / "fmv" / f"{m}.tsv"
        lines = f.read_text(encoding="utf-8").splitlines()
        assert lines[0].split("\t")[5] == "en", f
        for i, ln in enumerate(lines[1:], 1):
            c = ln.split("\t")
            if (m, c[0]) in fix:
                c[5] = fix[m, c[0]]
                done.add((m, c[0]))
                lines[i] = "\t".join(c)
        f.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    assert done == set(fix), f"no row for {sorted(set(fix) - done)}"
    print(len(done), "rows set")


if __name__ == "__main__":
    main(sys.argv[1])
