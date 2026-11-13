"""build.py: make the disc in build/ from rom/.

usage: build.py [OUTDIR] [--identity | --en [--no-staff] | --marker | --spike [--no-staff]]
--en is the English disc (build/en, see english()).
Every form 1 file goes back through disc.write_file, every TIMP archive through timp.unpack/pack and every TIM in it
through tim.pixels/with_pixels, so with no edits the output must equal the dump: tests/test_build.py holds that.
An entry whose bytes are unchanged keeps its original BPE stream; a changed one is re-encoded (timp.bpe_encode) and the
archive is zero-padded back to its old size, as files can't move (disc.write_file); a grown archive stops the build.
Edits are keyed by TIM blob sha1 (tools/gfx.py), so every copy of a sprite changes, in TIMP archives and in
GRAP/MODE1.TMP (plain TIMs back to back).
--marker paints every graphics.tsv rect with its row number and burns a test line into every movie (build/marker);
--spike letters script/spike.tsv in English (build/spike).
"""
import hashlib
import shutil
import sys
from pathlib import Path

import check_rom
import disc
import tim
import timp

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom"
NAME = "Time Bokan Series - Bokan GoGoGo (Japan)"
BIN, CUE = NAME + ".bin", NAME + ".cue"


def rebuild_tim(b):
    t = tim.parse(b, strict=False)
    return tim.with_pixels(t, b, tim.pixels(t, b)) if t else b


def blob_edit(edits):
    """edit(i, blob) applying edits {sha1: fn(blob) -> blob}."""
    def edit(i, b):
        f = edits.get(hashlib.sha1(b).hexdigest())
        return f(b) if f else b
    return edit


def rebuild_timp(data, edit=lambda i, b: b):
    """edit(i, blob) -> blob for entry i; unchanged entries keep their compressed bytes."""
    old = timp.unpack(data)
    comp = [data[o:o + c] for o, _, c in timp.entries(data)]
    new = [edit(i, rebuild_tim(b)) for i, b in enumerate(old)]
    out = timp.pack(new, [c if n == b else timp.bpe_best(n) for n, b, c in zip(new, old, comp)], timp.align_of(data))
    assert len(out) <= len(data), f"archive grew {len(data)} -> {len(out)}: needs a relocating disc writer"
    return out.ljust(len(data), b"\0")


def rebuild_plain(data, edit):
    """GRAP/MODE1.TMP: TIMs back to back, each the same size after an edit (pixels only)."""
    out, off = bytearray(), 0
    while off < len(data) and (t := tim.parse(data, off)):
        out += edit(0, data[off:off + t.size])
        off += t.size
    out += data[off:]
    assert len(out) == len(data)
    return bytes(out)


def build(out=None, identity=True, edits=None, after=None):
    """Returns the path of the new cue. edits: {sha1: fn(blob) -> blob}; after(bin_path) runs on the written image."""
    assert identity or edits is not None
    check_rom.check()
    out = Path(out or ROOT / "build" / "identity")
    out.mkdir(parents=True, exist_ok=True)
    for name in (BIN, CUE):
        shutil.copyfile(ROM / name, out / name)
    edit = blob_edit(edits) if edits else None
    d = disc.Disc(str(out / BIN), write=True)
    for e in d.files.values():
        if d.is_xa(e):
            continue
        data = d.read(e.path)
        if data[:4] == timp.MAGIC:
            data = rebuild_timp(data, edit) if edit else rebuild_timp(data)
        elif edit and tim.parse(data, 0):
            data = rebuild_plain(data, edit)
        d.write_file(e.path, data)
    d.f.close()
    if after:
        after(out / BIN)
    return out / CUE


ALLOWED = ROOT / "script" / "allowed.txt"  # committed spec: english() fails if its edits reach any other file


def allowed_files(edits, roll=True):
    """Disc paths the English build may change: every file holding an edited blob, DEMO.BIN (save titles), the movies
    with English subtitle rows, and STAFF.STR when the roll is re-lettered."""
    import fmv_burn
    import gfx_index
    d = disc.Disc(str(ROM / BIN))
    by_id = {p[1:].removesuffix(".TMP"): p for p in d.files}
    files = {by_id[i.split("#")[0]] for i, b in gfx_index.tims() if hashlib.sha1(b).hexdigest() in edits}
    movies = {p for p in d.files if p.startswith("/STR/") and fmv_burn.en_subs(Path(p).stem)}
    return files | {"/OVER/DEMO.BIN"} | movies | ({"/STR/STAFF.STR"} if roll else set())


def tim_errors(orig, new, edits):
    """Entry-level check of a built disc. orig, new: [(id, blob)] from gfx_index.tims of the dump and the build. Every
    copy of an edited blob must be its edit's output (no original copy left), every other TIM unchanged, and no TIM's
    header, CLUT or size may change."""
    if [i for i, _ in orig] != [i for i, _ in new]:
        return ["TIM ids differ between the dump and the build"]
    errs, want = [], {}
    for (i, a), (_, b) in zip(orig, new):
        h = hashlib.sha1(a).hexdigest()
        if h not in edits:
            if a != b:
                errs.append(f"{i}: unedited TIM changed")
            continue
        want.setdefault(h, edits[h](a))
        if b == a:
            errs.append(f"{i}: original copy of an edited blob left")
        elif b != want[h]:
            errs.append(f"{i}: not its edit's output")
        t = tim.parse(a, strict=False)
        if len(a) != len(b) or (t and a[:t.px_off] != b[:t.px_off]):
            errs.append(f"{i}: TIM header, CLUT or size changed")
    return errs


def allowed_spec():
    return {ln.split("#")[0].strip() for ln in ALLOWED.read_text(encoding="utf-8").splitlines()} - {""}


def english(out=None, roll=True):
    """The English disc in build/en: graphics_en.tsv lettered, subtitles burnt into BOGO02-18 (D7), save titles (D8),
    the STAFF.STR roll re-lettered (D3; roll=False skips its ~20 min re-encode). Fails on edits reaching a file not in
    script/allowed.txt, on any sector changed outside allowed_files (tools/discdiff.py), and on any TIM tim_errors
    flags."""
    import discdiff
    import fmv_burn
    import gfx
    import gfx_index
    import save_titles
    import staff_roll
    edits = gfx.spike_edits(gfx.EN)

    def after(track):
        save_titles.patch(track)
        print("subtitles", fmv_burn.burn_en(track))
        if roll:
            print("staff roll", staff_roll.rewrite(track))
    allowed = allowed_files(edits, roll)
    assert allowed <= allowed_spec(), f"edits reach files not in {ALLOWED.name}: {sorted(allowed - allowed_spec())}"
    cue = build(out or ROOT / "build" / "en", False, edits, after)
    (cue.parent / "allowed.txt").write_text("".join(p + "\n" for p in sorted(allowed)), encoding="utf-8")
    errs, per = discdiff.check(ROM / BIN, cue.parent / BIN, allowed)
    assert not errs, "\n".join(errs[:20])
    print(f"discdiff: {sum(per.values())} sectors changed in {len(per)} files, all allowed")
    orig, new = gfx_index.tims(ROM / BIN), gfx_index.tims(cue.parent / BIN)
    errs = tim_errors(orig, new, edits)
    assert not errs, "\n".join(errs[:20])
    n = sum(hashlib.sha1(b).hexdigest() in edits for _, b in orig)
    print(f"TIMs: {n} copies of {len(edits)} edited blobs replaced, the other {len(orig) - n} unchanged")
    return cue


if __name__ == "__main__":
    import gfx
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--en" in sys.argv:
        print(english(args[0] if args else None, "--no-staff" not in sys.argv))
    elif "--marker" in sys.argv:
        import fmv_burn
        print(build(args[0] if args else ROOT / "build" / "marker", False, gfx.marker_edits(), fmv_burn.burn_markers))
    elif "--spike" in sys.argv:
        import staff
        print(build(args[0] if args else ROOT / "build" / "spike", False, gfx.spike_edits(),
                    None if "--no-staff" in sys.argv else staff.spike))  # STAFF re-encode takes ~20 min
    else:
        print(build(args[0] if args else None, True))
