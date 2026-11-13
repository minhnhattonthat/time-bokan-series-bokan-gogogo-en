"""Contact sheets of a warp tour for visual QA: one sheet per scene (full size, unchanged frames dropped, 12 tiles a
page: <scene>.png, <scene>_2.png ...), for qa_gate.py init OUT --glob "*.png".

usage: qa_sheets.py TOURDIR OUTDIR [scene ...]     (e.g. work/qa/env work/qa/sheets_en; work/qa/warp work/qa/sheets_jp)"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill import SKILL  # noqa: E402


def main(tour, out, scenes):
    tour, out = Path(tour), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for d in sorted(p for p in tour.iterdir() if p.is_dir() and (not scenes or p.name in scenes)):
        shots = sorted(str(p) for p in d.glob("*.png"))
        if not shots:
            continue
        r = subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), *shots,
                            "--changed", "0.01", "--div", "1", "--max", "12", "--out", str(out / f"{d.name}.png")],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"{d.name}: {r.stderr.strip()}")
    print(len(list(out.glob("*.png"))), "sheets ->", out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
