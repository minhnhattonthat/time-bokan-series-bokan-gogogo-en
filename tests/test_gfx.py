"""Lettering: typeset changes pixels only inside its rect, refuses overflow, and the spike rows fit (width gate)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import fit
import gfx
import gfx_index
import gfx_script
import tim

needs_rom = pytest.mark.skipif(not (build.ROM / build.BIN).exists(), reason="needs the dump in rom/")


def test_rings_wrap_the_ink():
    ink, inner, outer = gfx.glyphs("Ab", "menu")
    assert not (ink & inner).any() and not (inner & outer).any() and not (ink & outer).any()
    assert inner.any() and outer.any()
    assert not gfx.glyphs("Ab", "label")[1].any()


def test_every_row_has_a_class():
    for r in gfx_script.rows():
        assert r.form in gfx.KEEP_FORMS or gfx.class_of(r) in gfx.CLASSES, r.id


@needs_rom
def test_typeset_stays_in_rect_and_refuses_overflow():
    r = {x.id: x for x in gfx_script.rows()}["MODE#2"]
    blob = dict(gfx_index.tims())[r.file]
    t = tim.parse(blob, strict=False)
    w = gfx.pixel_width(t)
    new = gfx.typeset(blob, [((r.x, r.y, r.w, r.h), "Story Mode", "menu")])
    a = np.array(tim.pixels(t, blob)).reshape(-1, w)
    b = np.array(tim.pixels(t, new)).reshape(-1, w)
    changed = np.argwhere(a != b)
    assert changed.size
    assert changed[:, 0].min() >= r.y and changed[:, 0].max() < r.y + r.h
    assert changed[:, 1].min() >= r.x and changed[:, 1].max() < r.x + r.w
    with pytest.raises(ValueError):
        gfx.typeset(blob, [((r.x, r.y, r.w, r.h), "Story Mode Story Mode Story Mode", "menu")])


@needs_rom
def test_list_rows_keep_the_japanese_left_anchor():
    r = {x.id: x for x in gfx_script.rows()}["STAT01#93"]  # リスタート in the pause list, 66 px of a wider TIM
    assert gfx.left_anchored(r)
    blob = dict(gfx_index.tims())[r.file]
    t = tim.parse(blob, strict=False)
    w = gfx.pixel_width(t)

    def ink_span(left):
        b = np.array(tim.pixels(t, gfx.typeset(blob, [((r.x, r.y, r.w, r.h), "Go", "label", left)]))).reshape(-1, w)
        cols = np.flatnonzero((b[r.y:r.y + r.h] != b[r.y:r.y + r.h, r.x + r.w - 1:r.x + r.w]).any(axis=0))
        return cols.min(), cols.max()
    lo, hi = ink_span(True)
    assert lo <= r.x + 1 and hi < r.x + r.w // 2  # short English sits at the Japanese start, not mid-rect
    assert ink_span(False)[0] > lo + 10


def test_inpainted_fills_from_known_neighbours():
    px = np.array([[1, 1, 1, 2], [1, 9, 9, 2], [3, 3, 3, 3]])
    out = gfx.inpainted(px, px != 9)
    assert (out != 9).all() and out[1, 1] == 1 and out[1, 2] == 2  # left/right neighbours, not the row below


@needs_rom
def test_title_fill_has_no_outline_bands():
    """MACHINE DATA (thick orange outline, yellow-white gradient): no outline-coloured rows cross the English strokes,
    and the gradient runs top to bottom (phase 8 stripes: per-row fill sampled at the same y as the Japanese)."""
    r = {x.id: x for x in gfx_script.rows()}["MODE#89"]
    blob = dict(gfx_index.tims())[r.file]
    t = tim.parse(blob, strict=False)
    w = gfx.pixel_width(t)
    b = np.array(tim.pixels(t, gfx.typeset(blob, [((r.x, r.y, r.w, r.h), "MACHINE DATA", "title")]))).reshape(-1, w)
    ink = gfx.glyphs("MACHINE DATA", "title")[0]
    gh, gw = ink.shape
    oy, ox = r.y + (r.h - gh) // 2, r.x + (r.w - gw) // 2
    letters = b[oy:oy + gh, ox:ox + gw][ink]
    assert 1 not in letters.tolist()  # index 1 = the orange outline
    rows = [gfx.mode(b[oy + y, ox:ox + gw][ink[y]]) for y in range(gh) if ink[y].any()]
    assert rows[0] != rows[-1]


def test_spike_rows_fit():
    assert fit.check(ROOT / "script" / "spike.tsv") == 0


def test_translation_covers_every_row_and_fits():
    path = ROOT / "script" / "graphics_en.tsv"
    rows = [ln.split("\t") for ln in path.read_text(encoding="utf-8").splitlines()[1:]]
    want = [r.id for r in gfx_script.rows() if r.form not in gfx.KEEP_FORMS]
    assert [r[0] for r in rows] == want  # every lettered row once, in graphics.tsv order
    for rid, en, cls, rect in rows:
        assert en and en.replace("©", "").isascii() and "  " not in en, rid
        assert not cls or cls in gfx.CLASSES, rid
    assert fit.check(path) == 0  # no OVER; "grow" rows widen inside their TIM at build time (typeset grow)


def test_grown_rect_stays_in_its_tim():
    assert gfx.grown((10, 2, 20, 8), (30, 8), (64, 16)) == (5, 2, 30, 8)  # about the centre
    assert gfx.grown((0, 0, 20, 8), (30, 10), (64, 16)) == (0, 0, 30, 10)  # clamped at the left/top
    assert gfx.grown((50, 6, 14, 10), (30, 12), (64, 16)) == (34, 4, 30, 12)  # and at the right/bottom


@needs_rom
def test_every_english_row_letters():
    """The English build's graphics edits all apply: nothing overflows its (grown) rect, every edit changes pixels."""
    edits = gfx.spike_edits(gfx.EN)
    done = set()
    for _, b in gfx_index.tims():
        h = __import__("hashlib").sha1(b).hexdigest()
        if h in edits and h not in done:
            assert edits[h](b) != b
            done.add(h)
    assert done == set(edits)
