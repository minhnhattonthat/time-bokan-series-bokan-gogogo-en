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
