# Disc layout

Game: Time Bokan Series: Bokan GoGoGo (SLPS-03133), Banpresto 2001 (title screen (C) 2001), kart racing with the Time
Bokan villain teams. Not a sequel engine of Bokan desu yo (shooter): new formats throughout. No earlier fan patch found
(one web search; romhacking.net not checked).

**Verified** by `tools/disc.py list` and `tests/test_recon.py` unless marked.

- One track, MODE2/2352, 277,048 sectors (`.bin` + `.cue`). No CD audio: music is XA.
- `disc.py` (from desu-yo) reads the ISO9660 tree and rewrites form 1 files in place with fresh EDC/ECC.
- Boot: `SYSTEM.CNF` -> `SLPS_031.33` (PS-X EXE, load 0x80010000, 0x2E000 text, entry 0x80010EB8).

| Path | Count | What it is |
|---|---|---|
| `SLPS_031.33` | 1 | main program; TIMP loader and BPE decoder; no Japanese |
| `OVER/MOV_PLAY.BIN`, `CART.BIN`, `DEMO.BIN` | 3 | overlays; DEMO.BIN holds the memory card save titles (Shift-JIS) |
| `GRAP/*.TMP` | 73 | menus, results, story mode, save screens: almost all Japanese graphics text (`graphics.md`) |
| `STAGE/STAT*.TMP` | 40 | race HUD and pause menu, the same text sprites in each |
| `STAGE/CORCE*, COS_GP*, BOSS*` `.TMP/.BIN` | many | track textures (TMP) and course data (BIN, "BG  " chunks) |
| `CAR/*.TMP, *.TMD` | 44+ | kart textures and models, team face icons |
| `STR/BOGO01-18.STR` | 18 | movies: BOGO01 opening, the rest story scenes with spoken dialogue |
| `STR/STAFF.STR` | 1 | staff roll as a movie: scrolling Japanese credits over black with kart pictures |
| `XA/SND1-3.XA`, `XA/CAR0-6/AKU*.XA` | 101 | music; per-team voice clips in races (spoken, no on-screen text) |
| `SOUND/*.VH, *.VB` | many | VAB sound banks |

## TIMP archives (.TMP) - verified

`tools/timp.py`. `b"TIMP"`, then per entry three u32 LE: offset from file start, uncompressed size, compressed size;
an offset of -1 ends the list. Entries are packed back to back from the end of the header, files padded to 4 bytes.
Loaders 0x800143C4 and 0x800144F8 (`SLPS_031.33`) check the magic, then call 0x800141AC(src, dst, comp_size), which is
Philip Gage's byte pair encoding: blocks of [pair table][u16 BE size][size bytes] until comp_size bytes are used.

- All 197 TIMP files decode; every entry is a 4 or 8 bpp TIM (12,197 entries). `GRAP/MODE1.TMP` is not TIMP: 12 plain
  TIMs back to back.
- Some entries' TIM pixel-block length word is wrong (CAR, STAT): `tim.parse(b, strict=False)` ignores it.
- `timp.pack(blobs, comp)` rebuilds a file byte-identically from the original compressed bytes (test). `bpe_store` is a
  literal-only encoder (no pairs, input size + 5 per 64 KB block). Phase 5: `bpe_encode` is a real Gage encoder and
  `bpe_best` keeps the smallest of blocks 5,000/8,000/15,000. Limits it stays inside, measured over every block of every
  TIMP on the disc: at most 15,623 bytes out of one block, 6,198 packed bytes, decoder stack depth 78 (`bpe_encode`
  caps pair nesting at 64). Files keep their size (`disc.write_file` can't resize; load buffer sizes unknown), so the
  build zero-pads a smaller archive and stops on a larger one.

## Text

See `text.md`. Graphics survey: `graphics.md`.

## Not yet known (phase 2)
- Game state variables (mode, course, team, story progress) for the warp tool. No debug strings were looked for yet.
- Which TIMP entry is drawn where, and whether sprite UV/size tables live in code or data.
