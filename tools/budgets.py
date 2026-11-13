"""Width gate data: per graphics.tsv row, the rect (where the Japanese is), the TIM box around it, and whether other rows
share the TIM. Writes script/budgets.tsv.

usage: budgets.py [--print]
Columns: id, form, class, rect w x h, tim w x h, room_w x room_h, rows_in_tim, source. `source` says how the room is
known: `tim` = the row is its TIM's only one, and the marker build (which paints such TIMs whole) shows the game draws
the whole TIM, so the English may use all of it (re-centred); `rect` = the TIM holds other rows (or is art), so the
room is the rect. Neighbouring sprites can overlap a TIM's transparent margin (machine data panels): a row that needs
more than its rect gets a zoomed look at its marker shot (work/qa/marker) before phase 7 grows it."""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx
import gfx_index
import gfx_script

OUT = ROOT / "script" / "budgets.tsv"


def table():
    tims = {i: b for i, b in gfx_index.tims()}
    rows = gfx_script.rows()
    per_tim = Counter(r.file for r in rows)
    out = []
    for r in rows:
        if r.form in gfx.KEEP_FORMS:
            continue
        t = gfx_index.tim.parse(tims[r.file], strict=False)
        tw, th = gfx.pixel_width(t), t.px_wh[1]
        alone = per_tim[r.file] == 1
        span = alone and r.form != "art"
        out.append((r.id, r.form, gfx.class_of(r), r.w, r.h, tw, th,
                    tw if span else r.w, th if span else r.h, per_tim[r.file], "tim" if span else "rect"))
    return out


if __name__ == "__main__":
    rows = table()
    lines = ["id\tform\tclass\tw\th\ttim_w\ttim_h\troom_w\troom_h\trows_in_tim\tsource"]
    lines += ["\t".join(map(str, r)) for r in rows]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    grow = sum(1 for r in rows if r[7] > r[3] + 4)
    print(f"{len(rows)} rows; {grow} have 5+ px more room than the rect; {sum(r[9] > 1 for r in rows)} share a TIM")
