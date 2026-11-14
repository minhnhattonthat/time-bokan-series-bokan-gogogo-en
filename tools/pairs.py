"""JP/EN pairs files for reviewers (translation.md §Review): one file per kind, in screen/story order.

usage: pairs.py OUT_DIR   writes gfx.txt (unique graphics strings, ids and class), fmv.txt (every movie row with
speaker and note), credits.txt and save.txt. Lines read `>> id | speaker-or-form | JP` then `   EN`.
       pairs.py --chapters OUT_DIR   one story-pass file per chapter (CHAPTERS), for qa_gate's story manifest."""
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


# story pass chapters (docs/synopsis.md): team movie + ending per trio; the intro carries the briefings
CHAPTERS = {"00_intro": ["BOGO02", "DOKURO", "BOGO10"], "01_majo": ["BOGO03", "BOGO11"],
            "02_doronbow": ["BOGO04", "BOGO12"], "03_mujo": ["BOGO05", "BOGO13"], "04_atasha": ["BOGO06", "BOGO14"],
            "05_mirenjo": ["BOGO07", "BOGO15"], "06_munmun": ["BOGO08", "BOGO16"], "07_yanyan": ["BOGO09", "BOGO17"],
            "08_true": ["BOGO18"]}


def chapters(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    by_id = {r.id: r for r in gfx_script.rows()}
    brief = [(rid, en) for rid, en, *_ in tsv(ROOT / "script" / "graphics_en.tsv")
             if rid.startswith("DOKURO#") and 34 <= int(rid.split("#")[1].split(".")[0]) <= 74]
    for name, parts in CHAPTERS.items():
        with open(out / f"{name}.txt", "w", encoding="utf-8", newline="\n") as f:
            for part in parts:
                f.write(f"## {part}\n")
                if part == "DOKURO":
                    f.write("(briefing pieces, Dokurobey; joined at run time, e.g. 'First up:' + '<course>, y'hear')\n")
                    for rid, en in brief:
                        f.write(f">> {rid} | Dokurobey | {by_id[rid].jp}\n   {en}\n")
                    continue
                for start, end, form, speaker, jp, en, *note in tsv(ROOT / "script" / "fmv" / f"{part}.tsv"):
                    if form != "song":
                        f.write(f">> {part}@{start} | {speaker} | {jp}\n   {en}\n"
                                + (f"   note: {note[0]}\n" if note and note[0] else ""))
    print(len(CHAPTERS), "chapters;", out)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    chapters(sys.argv[2]) if sys.argv[1] == "--chapters" else main(sys.argv[1])
