"""build.py: make the disc in build/ from rom/.

usage: build.py [OUTDIR] --identity
Every form 1 file goes back through disc.write_file, every TIMP archive through timp.unpack/pack and every TIM in it
through tim.pixels/with_pixels, so with no edits the output must equal the dump: tests/test_build.py holds that.
An entry whose bytes are unchanged keeps its original BPE stream; a changed one is stored (timp.bpe_store).
The English edits come in phase 7; until then only --identity exists.
"""
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


def rebuild_timp(data, edit=lambda i, b: b):
    """edit(i, blob) -> blob for entry i; unchanged entries keep their compressed bytes."""
    old = timp.unpack(data)
    comp = [data[o:o + c] for o, _, c in timp.entries(data)]
    new = [edit(i, rebuild_tim(b)) for i, b in enumerate(old)]
    return timp.pack(new, [c if n == b else timp.bpe_store(n) for n, b, c in zip(new, old, comp)], timp.align_of(data))


def build(out=None, identity=True):
    """Returns the path of the new cue."""
    assert identity, "English build: phase 7"
    check_rom.check()
    out = Path(out or ROOT / "build" / "identity")
    out.mkdir(parents=True, exist_ok=True)
    for name in (BIN, CUE):
        shutil.copyfile(ROM / name, out / name)
    d = disc.Disc(str(out / BIN), write=True)
    for e in d.files.values():
        if d.is_xa(e):
            continue
        data = d.read(e.path)
        if data[:4] == timp.MAGIC:
            data = rebuild_timp(data)
        d.write_file(e.path, data)
    d.f.close()
    return out / CUE


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print(build(args[0] if args else None, "--identity" in sys.argv))
