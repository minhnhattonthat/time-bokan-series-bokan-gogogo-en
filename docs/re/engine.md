# Engine spike, marker build and width gate (phase 5)

No text engine: every change is pixels (TIMs, movie frames) or the 33 Shift-JIS save titles. So the "engine" work is
lettering, re-encoding and repacking, all in `tools/build.py`.

## Builds
- `build.py --identity` (phase 3): equals the dump.
- `build.py --marker` -> `build/marker`: every `script/graphics.tsv` row painted with its row number (line of
  graphics.tsv under the header, `python tools/gfx.py` prints the map), a dark box with a bright 1 px frame. A TIM that
  holds one row (not `art`) is painted **whole**, so the shot shows how much of it the game draws. Every movie with a
  script gets a two-line marker subtitle on each spoken row (`BOGOxx[4:].n` + a pangram) through `tools/fmv_burn.py`.
- `build.py --spike` -> `build/spike`: `script/spike.tsv` (one row per graphics form) lettered in English by
  `gfx.typeset`, and every STAFF.STR frame re-encoded as version 2 with an English test line (`tools/staff.py`).
- Edits are keyed by blob SHA-1 (`gfx.blob_edit`), so all 1,011 copies of the 453 text blobs change; a check after the
  marker build found 0 of the 441 edited blobs left in their original form anywhere on the disc. An edited TIMP entry is
  re-encoded with the game's BPE (`timp.bpe_encode`) and the archive zero-padded to its old size (files can't move);
  none grew.

## Marker tour (2026-11-14)
`warp_all.py --rom build/marker/... --out work/qa/marker`: **129/129 scenes ok**. Contact sheets
`work/qa/msheet/sheet*.png` (scene order = sorted directory names) read at half size, with zooms of `ta_menu`, a movie
and `true_ending`. Every listed sprite shows its marker; no Japanese left on screen except the kept logo (D5) and the
STAFF.STR roll (movie_18 in the viewer, `staff_roll`, `true_ending`), which the marker build does not touch. Subtitles:
two lines at 288 px, bottom line ends 12 px above the picture's edge, clear of the 16 px black strip below the 224-line
picture. Three lines were not shown (the pangram wraps to two).

## Width gate
- Graphics rows: `script/budgets.tsv` (`tools/budgets.py`). `w x h` = the rect (the Japanese ink box, drawn whole in
  the original). `room` = the whole TIM for a row that is alone in its TIM (`source tim`): the marker tour showed such
  TIMs drawn whole (e.g. `ta_menu`: course, machine and option sprites as full boxes). Shared TIMs and art keep the rect
  (`source rect`). Caveat: neighbours can overlap a TIM's transparent margin (machine data panels stack several TIMs),
  so a row that needs more than its rect gets a zoomed look at its marker shot before phase 7 widens it.
- `tools/fit.py TSV` is the check: `ok` fits the rect, `grow` fits only the room, `OVER` neither (exit 1). `gfx.typeset`
  refuses overflow at build time too.
- Fonts per class: D10, `CLASSES`/`FORM_CLASS`/`class_of` in `tools/gfx.py`; a translation row may name another
  class. Ink box heights (no descender / with): `bar` 12 / 15; `sign` (Jersey 10 + 2 outlines) 14 / 16; `label` 10 / 12;
  `menu` (Bangers 22 + 2 outlines) ~20; `small` (Tiny5) 5 / 7; `title` 28-29; `big` 25. Name rows (rect 11 px tall in
  16 px TIMs) need the whole TIM: "Majo" in `sign` is 33x16.
- Style choice: `tools/font_try.py ID TEXT OUT CLASS..` letters candidates into the real TIM beside the Japanese
  (ad-hoc `FONT:SIZE:o|oo`). Two outlines take the rect's darkest ink outside, its lightest inside and the commonest
  ink between as the fill (`gfx.typeset`); one outline samples per-row fill as before. Description panels are
  left-aligned in the original, typeset centres: phase 7 may want a left-align option there.
- Glyph torture sheet (`tools/torture.py work/qa/torture.png`, read at 3x): every printable ASCII glyph renders in
  every class; `|` is the line-break code, so it can't be used in text. Bangers has no lowercase (caps only).
  `credit` (Jersey 15 at 15 px, desu-yo's size) is off Jersey 15's native 27 px grid and looks uneven: pick the roll's
  font when STAFF.STR is re-lettered (antialiasing is fine there, it's a movie).
- Movie subtitles: 288 px wide, Liberation Serif Bold 13, 15 px pitch, two lines measured in game; `fmv_burn` refuses
  more than three. Phase 6 should keep to two.

## STAFF.STR (credits)
Version 3 frames (2,415, 320x240, 8-9 sectors each), which `mdec.py` can't edit. Plan: `staff.py decode` writes every
frame through ffmpeg (`work/fmv/STAFF/all/f%05d.png`), the roll is re-lettered on those pictures, and
`mdec.encode_rgb` writes each as a version 2 frame into the same sectors (audio untouched, words <= 13,472). A frame of
the roll at q 3 is ~8,000 words, well under the original's sizes. Spike result: see `docs/status.md`.
