"""FMV bitstream: an unedited frame comes out bit-exact, an edit stays inside its macroblocks, a whole picture encodes
as a version 2 frame that decodes back to it (STAFF.STR re-render), and the marker subtitles fit."""
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import disc
import fmv_burn
import mdec

needs_rom = pytest.mark.skipif(not (build.ROM / build.BIN).exists(), reason="needs the dump in rom/")


@pytest.fixture(scope="module")
def movie():
    d = disc.Disc(str(build.ROM / build.BIN))
    e = d.files["/STR/BOGO02.STR"]
    n = -(-e.size // 2048)
    raw = {i: d.raw(e.lba + i) for i in range(n)}
    return mdec.frames(raw.items()), raw.__getitem__


@needs_rom
def test_frames_roundtrip_bit_exact(movie):
    fr, sec = movie
    for f in fr[::97]:
        bs = mdec.frame_bytes(f, sec)
        assert mdec.Picture(bs, f.w, f.h).tobytes(len(bs)) == bs, f"frame {f.no}"


@needs_rom
def test_edit_touches_only_its_macroblock(movie):
    fr, sec = movie
    f = fr[100]
    p = mdec.Picture(mdec.frame_bytes(f, sec), f.w, f.h)
    before = list(p.blocks)
    _, cb, cr = p.get_mb(3, 11)
    p.set_mb(3, 11, np.full((16, 16), 100.0), cb, cr)
    i = (3 * p.rows + 11) * 6
    assert p.blocks[:i] == before[:i] and p.blocks[i + 6:] == before[i + 6:]
    y2, _, _ = mdec.Picture(p.tobytes(), f.w, f.h).get_mb(3, 11)
    assert abs(y2 - 100).max() < 4


def test_encode_rgb_decodes_back():
    rng = np.random.default_rng(1)
    rgb = np.zeros((48, 64, 3), np.uint8)
    rgb[8:40, 8:56] = rng.integers(0, 255, 3)  # flat coloured box on black, like the credit roll
    bs = mdec.encode_rgb(rgb, 2)
    assert struct.unpack_from("<4H", bs)[1:] == (0x3800, 2, 2)
    back = mdec.Picture(bs, 64, 48).rgb().astype(int)
    assert np.abs(back - rgb).mean() < 4


def test_marker_subtitles_fit():
    from PIL import ImageFont
    font = ImageFont.truetype(str(fmv_burn.FONT), fmv_burn.SIZE)
    lines = fmv_burn.balance(fmv_burn.wrap("18.30 " + fmv_burn.MARKER, font), font)
    assert len(lines) <= fmv_burn.MAX_LINES and all(font.getlength(ln) <= fmv_burn.MAX_W for ln in lines)
