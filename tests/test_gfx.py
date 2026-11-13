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
