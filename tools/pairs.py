"""JP/EN pairs files for reviewers (translation.md §Review): one file per kind, in screen/story order.

usage: pairs.py OUT_DIR   writes gfx.txt (unique graphics strings, ids and class), fmv.txt (every movie row with
speaker and note), credits.txt and save.txt. Lines read `>> id | speaker-or-form | JP` then `   EN`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx
import gfx_script


def tsv(path):
    return [ln.split("\t") for ln in path.read_text(encoding="utf-8").splitlines()[1:]]


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    by_id = {r.id: r for r in gfx_script.rows()}
    seen, lines = {}, []
    for rid, en, cls, rect in tsv(ROOT / "script" / "graphics_en.tsv"):
        r = by_id[rid]
        key = (r.jp, en)
        if key in seen:
            seen[key].append(rid)
            continue
        seen[key] = ids = [rid]
        lines.append((ids, f"{r.form}/{cls or gfx.class_of(r)} {r.w}x{r.h}", r.jp, en, r.note))
    with open(out / "gfx.txt", "w", encoding="utf-8", newline="\n") as f:
        for ids, form, jp, en, note in lines:
            more = f" (+{len(ids) - 1} copies)" if len(ids) > 1 else ""
            f.write(f">> {ids[0]}{more} | {form} | {jp}\n   {en}\n" + (f"   note: {note}\n" if note else ""))
    with open(out / "fmv.txt", "w", encoding="utf-8", newline="\n") as f:
        for p in sorted((ROOT / "script" / "fmv").glob("*.tsv")):
            f.write(f"## {p.stem}\n")
            for start, end, form, speaker, jp, en, *note in tsv(p):
                if form != "song":
                    f.write(f">> {p.stem}@{start} | {speaker} | {jp}\n   {en}\n"
                            + (f"   note: {note[0]}\n" if note and note[0] else ""))
    with open(out / "credits.txt", "w", encoding="utf-8", newline="\n") as f:
        for n, group, kind, jp, en, *note in tsv(ROOT / "script" / "credits.tsv"):
            f.write(f">> {n} | {kind} | {jp}\n   {en}\n")
    with open(out / "save.txt", "w", encoding="utf-8", newline="\n") as f:
        for n, off, jp, en in tsv(ROOT / "script" / "save_titles.tsv"):
            f.write(f">> {n} | save title | {jp}\n   {en}\n")
    print(len(lines), "graphics strings;", out)


if __name__ == "__main__":
    main(sys.argv[1])
