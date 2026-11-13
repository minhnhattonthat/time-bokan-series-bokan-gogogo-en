"""STAFF.STR, the credit roll movie: its frames are STR version 3, which tools/mdec.py can't edit, so the roll is
re-rendered: ffmpeg decodes every frame to a PNG, a paint function changes the picture, and mdec.encode_rgb writes a
version 2 frame back into the same sectors (each frame keeps its sector count; audio sectors stay).

usage: staff.py decode BIN OUT_DIR   (every frame as OUT_DIR/f%05d.png, frame n of the movie = file n+1)
Library: rewrite(track, frames_dir, paint) where paint(n, rgb) -> rgb or None (None keeps the original frame)."""
import os
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import disc
import mdec

PATH = "/STR/STAFF.STR"
FRAMES = ROOT / "work" / "fmv" / "STAFF" / "all"
Q = 3  # the roll's commonest qscale
WORDS_MAX = 13472  # same player buffer bound as tools/fmv_burn.py (largest original frame, BOGO17)


def decode(track, out=FRAMES):
    d = disc.Disc(str(track))
    e = d.files[PATH]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "STAFF.raw"
    with open(raw, "wb") as f:
        for i in range(-(-e.size // 2048)):
            f.write(d.raw(e.lba + i))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "psxstr", "-i", str(raw), "-fps_mode", "passthrough",
                    str(out / "f%05d.png")], check=True)
    raw.unlink()
    return out


def rewrite(track, paint, frames_dir=FRAMES):
    """Re-encodes every frame paint() changes. Returns (frames written, highest qscale used)."""
    d = disc.Disc(str(track))
    e = d.files[PATH]
    n = -(-e.size // 2048)
    raw = {i: d.raw(e.lba + i) for i in range(n)}
    d.f.close()
    frames = mdec.frames(raw.items())
    pngs = sorted(Path(frames_dir).glob("f*.png"))
    assert len(pngs) == len(frames), f"{len(pngs)} decoded pictures for {len(frames)} frames: run staff.py decode"
    out, top = {}, 0
    for f, png in zip(frames, pngs):
        rgb = paint(f.no, np.array(Image.open(png).convert("RGB")))
        if rgb is None:
            continue
        assert rgb.shape == (f.h, f.w, 3)
        cap, q = f.chunks * mdec.CHUNK, Q
        while len(new := mdec.encode_rgb(rgb, q)) > cap or struct.unpack_from("<H", new)[0] > WORDS_MAX:
            q += 1
            assert q <= mdec.MAX_Q
        top = max(top, q)
        for idx, i in enumerate(f.sectors):
            sec = bytearray(raw[i])
            struct.pack_into("<I", sec, 36, len(new))
            sec[44:52] = new[:8]
            sec[56:56 + mdec.CHUNK] = new[idx * mdec.CHUNK:(idx + 1) * mdec.CHUNK].ljust(mdec.CHUNK, b"\0")
            disc.form1_seal(sec)
            out[e.lba + i] = bytes(sec)
    with open(track, "r+b") as fh:
        for lba, sec in out.items():
            fh.seek(lba * disc.SECTOR)
            fh.write(sec)
    return len(out) and sum(1 for f in frames if e.lba + f.sectors[0] in out), top


def spike(track):
    """build.py --spike: every frame re-encoded as version 2 with an English test line, to prove the player takes
    version 2 frames in this movie and the roll still plays in time."""
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype(str(ROOT / "fonts" / "Jersey15-Regular.ttf"), 27)

    def paint(n, rgb):
        im = Image.fromarray(rgb)
        ImageDraw.Draw(im).text((160, 200), f"v2 frame {n}  Storyboard", font=font, fill=(255, 255, 255), anchor="ms")
        return np.array(im)
    return rewrite(track, paint)


if __name__ == "__main__":
    if sys.argv[1:2] == ["decode"]:
        print(decode(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else FRAMES))
    else:
        sys.exit(__doc__)
