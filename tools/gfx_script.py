"""script/graphics.tsv (one row per Japanese line drawn in a TIM) and script/no_text.txt (every other TIM).

usage: gfx_script.py draft SPEC.tsv     write both files from a hand spec (tim, form, jp lines split by |, note)
       gfx_script.py sheet OUT_PREFIX [--form F] [--ids FILE]   row crops, zoomed and labelled, to check by eye

graphics.tsv columns: id file x y w h form jp note. `file` is the canonical TIM id (gfx_index.py: the first
ARCHIVE#entry with that blob); every copy of the same blob elsewhere on the disc gets the same English by hash.
A spec line `jp@x,y,w,h` gives its rect by hand; otherwise rects come from gfx_sheet.inklines (one band per line),
or, when the bands don't match the line count, the ink box split into equal bands (noted).
no_text.txt lines: ARCHIVE (all its TIMs) or ARCHIVE#a-b / ARCHIVE#n. The draft overwrites both files: after
phase 4 graphics.tsv is the source and is edited by hand."""
import argparse
import sys
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_index
import gfx_sheet

GFX = ROOT / "script" / "graphics.tsv"
NO_TEXT = ROOT / "script" / "no_text.txt"
Row = namedtuple("Row", "id file x y w h form jp note")


def rows(path=GFX):
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        assert len(c) in (8, 9), f"bad row: {ln}"
        out.append(Row(c[0], c[1], *map(int, c[2:6]), c[6], c[7], c[8] if len(c) == 9 else ""))
    return out


def no_text(path=NO_TEXT, archives=None):
    """Expand no_text.txt to a set of TIM ids; `archives` maps ARCHIVE -> entry count."""
    out = set()
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#"):
            continue
        name, _, r = ln.partition("#")
        lo, _, hi = r.partition("-")
        rng = range(archives[name]) if not r else range(int(lo), int(hi or lo) + 1)
        out |= {f"{name}#{i}" for i in rng}
    return out


def compact(ids, counts):
    """Inverse of no_text(): whole archives as one line, else runs."""
    by = {}
    for i in ids:
        a, n = i.split("#")
        by.setdefault(a, []).append(int(n))
    out = []
    for a in sorted(by):
        ns = sorted(by[a])
        if len(ns) == counts[a]:
            out.append(a)
            continue
        lo = prev = ns[0]
        for n in ns[1:] + [None]:
            if n != prev + 1 if n is not None else True:
                out.append(f"{a}#{lo}" if lo == prev else f"{a}#{lo}-{prev}")
                lo = n
            prev = n
    return out


def split(img, n):
    """n line rects for img: one line = the sprite's opaque box; several = ink bands (gfx_sheet.ink)."""
    if n == 1:
        bb = img.getchannel("A").getbbox()
        return [(bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1])], ""
    for gap in (1, 0):
        rs = gfx_sheet.inklines(img, gap)
        if len(rs) == n:
            return rs, ""
    bb = gfx_sheet.ink(img).getbbox() or (0, 0, *img.size)  # opaque with no off-frame colour: whole TIM
    if n == 1:
        return [(bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1])], ""
    h = (bb[3] - bb[1]) / n
    return [(bb[0], bb[1] + round(k * h), bb[2] - bb[0], round((k + 1) * h) - round(k * h)) for k in range(n)], \
        "rect split evenly"


def draft(spec):
    items = gfx_index.tims()
    blob = dict(items)
    idx = gfx_index.index(items)
    canon = {i: c for i, _, _, c in idx}
    sha = {i: h for i, h, _, _ in idx}
    counts = {}
    for i, _ in items:
        a = i.split("#")[0]
        counts[a] = counts.get(a, 0) + 1
    out, text_hashes = ["id\tfile\tx\ty\tw\th\tform\tjp\tnote"], set()
    for ln in Path(spec).read_text(encoding="utf-8").splitlines()[1:]:
        tim_id, form, jp, *note = ln.split("\t")
        note = note[0] if note else ""
        assert canon.get(tim_id) == tim_id, f"{tim_id} is not a canonical TIM id (copy of {canon.get(tim_id)})"
        assert sha[tim_id] not in text_hashes, f"{tim_id} twice"
        text_hashes.add(sha[tim_id])
        img = gfx_sheet.render(blob[tim_id])
        lines = jp.split("|")
        given = [ln_.partition("@") for ln_ in lines]
        if all(g[1] for g in given):
            rects, how = [tuple(map(int, g[2].split(","))) for g in given], ""
        else:
            assert not any(g[1] for g in given), f"{tim_id}: give every rect or none"
            rects, how = split(img, len(lines))
        base = tim_id.split("/", 1)[1]
        for k, ((text, _, _), r) in enumerate(zip(given, rects)):
            rid = base if len(lines) == 1 else f"{base}.{k + 1}"
            nt = "; ".join(x for x in (note, how) if x)
            out.append("\t".join([rid, tim_id, *map(str, r), form, text, nt]).rstrip("\t"))
    GFX.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    rest = [i for i, _ in items if sha[i] not in text_hashes]
    head = "# TIMs with no Japanese to translate (gfx_script.py; docs/re/graphics.md). Every other TIM's blob has rows in graphics.tsv.\n"
    NO_TEXT.write_text(head + "\n".join(compact(rest, counts)) + "\n", encoding="utf-8", newline="\n")
    print(len(out) - 1, "rows,", len(text_hashes), "text blobs,", len(items) - len(rest), "TIMs with text,",
          len(rest), "without")


def sheet(prefix, form=None, ids=None):
    from PIL import Image, ImageDraw, ImageFont
    blob = dict(gfx_index.tims())
    rs = [r for r in rows() if (not form or r.form == form) and (not ids or r.id in ids)]
    try:  # the reading under each crop, for review; Windows font, else no reading
        jpf = ImageFont.truetype("msgothic.ttc", 12)
    except OSError:
        jpf = None
    cols, cw, ch, per = 5, 260, 84, 100
    for p in range(0, len(rs), per):
        chunk = rs[p:p + per]
        img = Image.new("RGB", (cols * cw, (len(chunk) + cols - 1) // cols * ch), (90, 0, 90))
        d = ImageDraw.Draw(img)
        for k, r in enumerate(chunk):
            crop = gfx_sheet.render(blob[r.file]).crop((r.x, r.y, r.x + r.w, r.y + r.h))
            z = max(1, min((cw - 4) // r.w, (ch - 28) // r.h))
            crop = crop.resize((r.w * z, r.h * z), Image.NEAREST)
            x, y = k % cols * cw, k // cols * ch
            d.text((x + 2, y), r.id[:40], fill=(255, 255, 0))
            if jpf:
                d.text((x + 2, y + 12), r.jp[:20], fill=(0, 255, 255), font=jpf)
            img.paste(crop, (x + 2, y + 26), crop)
        out = f"{prefix}_{p // per}.png"
        img.save(out)
        print(out, len(chunk))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["draft", "sheet"])
    ap.add_argument("arg")
    ap.add_argument("--form")
    ap.add_argument("--ids")
    a = ap.parse_args()
    if a.cmd == "draft":
        draft(a.arg)
    else:
        sheet(a.arg, a.form, open(a.ids).read().split() if a.ids else None)
