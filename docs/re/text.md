# Text engine

**There is no text engine.** Apart from the memory card titles, every Japanese string is pixels: a TIM entry inside a
TIMP archive (`graphics.md`) or a frame of an STR movie.

**Verified:**
- `jpscan.py` on `SLPS_031.33`, `OVER/MOV_PLAY.BIN`, `OVER/CART.BIN`: no Japanese (a few Shift-JIS hits are noise:
  `幤暾晰練溟蛸` and its reverse are data tables; UTF-16 hits are pointer tables).
- `OVER/DEMO.BIN` 0xBC8-0x148B: memory card save titles, Shift-JIS full width, 0x44 bytes apart, padded with U+3000:
  `ボカンＧＯＧＯＧＯ` and 32 of `ボカンＧＯＧＯＧＯ／<course>・ファイル１|２` (16 courses x 2 files). Shown only by the BIOS
  memory card manager. Translate in full-width ASCII, same length (`tests/test_recon.py` counts them).

So:
- Pointers, control codes, table files: none. `tbl/` stays empty.
- Script source for translators: Japanese read from the images (phase 4), plus the 33 save titles.
- Roundtrip test (phase 4): TIMP entries decode and re-pack byte-identically; TIM pixels roundtrip.

## Voice (no on-screen text)
BOGO02-18 tell the story in spoken Japanese with no subtitles, and the race voice clips (`XA/CAR*/AKU*.XA`) are spoken
taunts. The movies need burned-in subtitles (as in bokan-desu-yo, D7 there); the race clips are left as voice.
STAFF.STR carries the credits as video: English credits mean re-rendering that movie (phase 5 spike).
