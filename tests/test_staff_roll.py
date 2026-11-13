"""STAFF.STR roll in English: every credits.tsv row finds its Japanese line in the stitched roll, and a painted frame
keeps the picture outside the text column."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import staff_roll  # noqa: E402

needs_frames = pytest.mark.skipif(not staff_roll.STRIP.exists(),
                                  reason="needs work/fmv/STAFF (staff.py decode, staff_roll.py strip)")


@needs_frames
def test_layout_places_every_credit():
    lay = staff_roll.layout()  # asserts order, columns and actors beside their roles itself
    assert len(lay) == len(staff_roll.credits()) == 202
    assert all(row[2] != "role" or b < staff_roll.MID for row, _, _, _, b in lay)


@needs_frames
def test_english_strip_stays_on_screen():
    ink, _ = staff_roll.english_strip()
    cols = np.flatnonzero(ink.any(axis=0))
    assert cols[0] >= 8 and cols[-1] < staff_roll.RIGHT


@needs_frames
def test_paint_changes_only_the_text_column():
    p = staff_roll.Painter()
    n = 600
    a = p.frame(n)
    b = p(n, a)
    diff = np.argwhere((a != b).any(axis=2))
    assert diff.size and diff[:, 1].min() >= staff_roll.X0 - 12
