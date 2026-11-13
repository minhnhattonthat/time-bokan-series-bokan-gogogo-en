"""build.py: make the disc in build/ from rom/.

usage: build.py [OUTDIR] [--identity | --marker | --spike]
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


if __name__ == "__main__":
    import gfx
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--marker" in sys.argv:
        import fmv_burn
        print(build(args[0] if args else ROOT / "build" / "marker", False, gfx.marker_edits(), fmv_burn.burn_markers))
    elif "--spike" in sys.argv:
        import staff
        print(build(args[0] if args else ROOT / "build" / "spike", False, gfx.spike_edits(),
                    None if "--no-staff" in sys.argv else staff.spike))  # STAFF re-encode takes ~20 min
    else:
        print(build(args[0] if args else None, True))
