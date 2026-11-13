"""Width gate offline: each row of a translation tsv (id, en, class, rect) against its rect, in its class's font.

usage: fit.py [TSV]   (default script/spike.tsv); exit 1 if any row overflows. Budget = the row's rect in
script/graphics.tsv (the sprite's drawn span, checked on the marker build), so this is the check translators run."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx
import gfx_script


def check(path):
    """ok = fits the rect; grow = fits only the room (script/budgets.tsv), phase 7 widens the rect; OVER = neither."""
    by_id = {r.id: r for r in gfx_script.rows()}
    room = {c[0]: (int(c[7]), int(c[8])) for c in (ln.split("\t") for ln in
            (ROOT / "script" / "budgets.tsv").read_text(encoding="utf-8").splitlines()[1:])}
    bad = 0
    for ln in Path(path).read_text(encoding="utf-8").splitlines()[1:]:
        rid, en, cls, rect = (ln.split("\t") + [""] * 4)[:4]
        r = by_id[rid]
        cls = cls or gfx.class_of(r)
        w, h = map(int, rect.split(",")[2:]) if rect else (r.w, r.h)
        rw, rh = room[rid] if not rect else (w, h)
        gw, gh = gfx.row_size(en, cls)
        verdict = "ok" if gw <= w and gh <= h else "grow" if gw <= rw and gh <= rh else "OVER"
        bad += verdict == "OVER"
        print(verdict, rid, cls, f"{gw}x{gh} in {w}x{h} (room {rw}x{rh})", en, sep="\t")
    return bad


if __name__ == "__main__":
    sys.exit(1 if check(sys.argv[1] if len(sys.argv) > 1 else ROOT / "script" / "spike.tsv") else 0)
