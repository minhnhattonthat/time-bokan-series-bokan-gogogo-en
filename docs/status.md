# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator next: phase 7 (insert, fit, check) done 2026-11-14.
- **Phase 7 (done 2026-11-14):** `python -X utf8 tools/build.py --en` -> `build/en/` (~30 min; `--no-staff` ~6 min
  skips the roll). Last build 07:34, bin sha1 `2b68bc19cd5a84fdadf883e5b8c3d34c44b63905`.
  - Graphics: `gfx.spike_edits(gfx.EN)` letters all 495 rows; a TIM's only row (fit.py `grow`) widens about its
    centre inside the TIM at build time (`gfx.grown`, `typeset(grow=True)`), no rect edits needed. Tests
    `test_gfx.py::test_every_english_row_letters`, `test_grown_rect_stays_in_its_tim`.
  - Subtitles: `fmv_burn.en_subs` (en column) into BOGO02-18: 11,190 frames burnt, up to +4 qscale.
  - Save titles: `save_titles.english/patch` into /OVER/DEMO.BIN; `jp_left.py --sjis` on the built DEMO.BIN: 0 runs
    (original 54). Test `test_script.py::test_english_save_titles_land_in_their_fields`.
  - STAFF roll: `tools/staff_roll.py` (strip | bands | layout | shot OUT N.. | drift). The roll scrolls 2.225 px/frame
    to frame 2340, then holds and fades. The stitched strip (`work/fmv/STAFF/strip.png`, 30th percentile per row)
    gives clean text; its lines match all 202 credits rows in order (roles right-aligned left of x 212, actors right,
    centred heads/names; the final card is centred on screen). Each frame: Japanese ink filled from a frame ±4-20
    where the text has moved on, English (Liberation Sans Bold 12, ◆ drawn as polygons, `<Anime R>` subs) drawn with
    a soft dark halo, faded with the original after the stop. All 2,415 frames re-encoded v2; highest qscale 12 (the
    wave frames; check zoomed in phase 8). Needs `staff.py decode` frames in `work/fmv/STAFF/all` (strip builds
    itself). Tests `tests/test_staff_roll.py` (skip without the frames).
  - Checks: `tools/discdiff.py` (sector-level romdiff, the skill's romdiff.py is per-byte Python and can't take a
    650 MB disc): 122,040 sectors changed in 75 files, all in `build/en/allowed.txt` (edited TIMP archives, DEMO.BIN,
    /STR/*), headers untouched. No text engine, so no control codes. `tools/check.py` 33 passed. Smoke ok
    (`work/qa/en_smoke`). Warp tour on build/en: **129/129 scenes ok** (`work/qa/en/<scene>/final.png`); a 9-shot
    half-size look (title, mode select, machine select, machine data, movies tab, pause, team movie subtitle, GP
    results) shows English everywhere, nothing zoomed yet.
- **Next (phase 8):** zoomed visual QA of the en tour with `qa_gate.py` manifests and read-only verdicts (self or
  `codex exec`; no subagents in Orca): every graphics row in a cold-boot shot, chapter cards/briefings c0-c7, game over,
  credits roll frames (wave frames at high qscale), subtitles in every movie, `inkbox.py` on menus. Items to look for:
  grown rows overlapping neighbouring sprites, description panels centred where the Japanese was left-aligned
  (left-align option if it reads badly), briefing pieces DOKURO#34-74 joined at run time (capital after "At last,"),
  MODE1#1.2-1.3 at 152 px against the panel border. `textcover.py` needs a text-read log; graphics-only game, so
  coverage = every graphics row seen in a shot. Write `docs/synopsis.md` before phase 9.
- **Phase 6 (done 2026-11-14):** translated by one agent (no subagents in the Orca run), reviewed by `codex exec`.
  - Graphics: `script/graphics_en.tsv` (id, en, class, rect; the spike format, so `fit.py` and `gfx.spike_edits` read
    it): 495 rows, `fit.py` 0 OVER, 70 `grow` (fit only their measured room; phase 7 widens the rect). Test
    `test_gfx.py::test_translation_covers_every_row_and_fits`. New classes `narrow`/`narrowlabel` (Tiny5 drawn twice as
    tall, D11) for character names, movie tabs, スカ, 逆走行, two song titles; MSELECT plates in caps. Course names
    re-punned to fit (glossary Places). SAVE#7 letters only the misspelt word (rect 104,1,67,15).
  - Movies: `en` column after `jp` in `script/fmv/BOGO02-18.tsv`, 292 rows, each 2 lines max at 288 px
    (`test_mdec.py::test_english_subtitles_fit_two_lines`). `tools/fmv_set.py FIX.tsv` sets rows by movie and start.
  - Credits: `en` column in `script/credits.tsv` (202 lines, Western name order). Save titles: `en` column in
    `script/save_titles.tsv`, full width, course padded to 15 like the JP column, then ＃１/＃２; `tbl/save.tbl` has
    the full-width Latin letters and ＃; the test round-trips every English title through the table into 64 bytes.
  - Style: `docs/style-reference.md` (desu-yo's voices + this game's trios), `docs/reviewer-brief.md`,
    `tools/pairs.py OUT` (gfx/fmv/credits/save pairs files). Decisions D11 (narrow class), D12 (", y'hear", -sama,
    Top Billing). Cuts and font mixes for the in-game look: `docs/polish.md`.
  - Review: independent `codex exec` (read-only) of all four pairs files (`work/review/phase6_codex.txt`): 0 Critical,
    13 Important (voice lost in 3 subtitles, the pearl-skin gag set up too early, two machine-description lines,
    "Gyakuten!" left untranslated, 5 credit names against published credits), 11 Minor; all applied (subtitles via
    `work/review/phase6_fmv_fixes.tsv`). Save titles now keep the spaces: `<course padded to 15>　＃１`.
    Second pass (`phase6_codex2.txt`): every earlier finding fixed but two Important left (Ryuko's parentage,
    DOKURO#54 without the tic) and 3 Minor; all applied ("the dragon god's girl / Ryuko powers it!", "Good,
    y'hear!", ゴール = "Finish!").
    Harness review (`.harness/reviews/...-phase6.md`, 4 Important) applied: MODE1#1 "Itadakiman's Ryuko, / dragon
    god's daughter, / powers this mystic car!" (lines 2-3 widened to 4,y,152 inside the panel border), BOGO13@86.22
    "You're round as pearls, the lot of you!", DOKURO#54 "Bravo, y'hear!", MODE1#4 "built tough, it races / through
    time!", MODE1 third lines all end "!", save titles "ＢＯＫＡＮ　ＧＯＧＯＧＯ"; new lint
    `test_script.py::test_glossary_and_charset` (Avoid spellings, JP term => EN form, 様/さん, Dokurobey's tic, ASCII
    but ©; waivers in `GLOSSARY_WAIVED`). Third codex pass over every line changed since p6b (`phase6_codex3.txt`):
    1 Important (MODE1#1), fixed; fourth pass (`phase6_codex4.txt`): **Assessment: Approved**.
    `docs/synopsis.md` still to write before phase 9 (story pass chapter list).
- **Phase 5 (done 2026-11-14):** details in `docs/re/engine.md`.
  - Marker build (`build.py --marker`): every graphics row painted with its row number (single-row TIMs painted whole to show the drawn span), marker subtitles in BOGO02-18. 441 edited blobs, 0 original copies left on the disc. Tour `work/qa/marker`: **129/129 scenes ok**; sheets `work/qa/msheet/` read (half size, zooms of `ta_menu`, a movie, `true_ending`): every listed sprite marked, no Japanese left but the logo (D5) and STAFF.STR.
  - Fonts (D10): classes `title`/`big`/`menu` (Bangers 34/28/22), `bar` (Liberation Sans Bold 14), `sign`/`label` (Jersey 10 at native 18.67, double outline / plain), `small` (Tiny5 8, added to `fonts/`), subtitles Liberation Serif Bold 13. Chosen with `tools/font_try.py` on the real TIMs; `gfx.typeset` now does a double outline (darkest out, lightest in, commonest mid ink as fill). Spike builds (`build.py --spike`, `script/spike.tsv`, 27 rows, one or more per form) toured: `work/qa/spike` (128/129, `game_over` failed once with a Lua coroutine error and passed on rerun), `work/qa/spike2` (17 scenes). English seen in game on mode select, machine data, movie tabs, course select, machine select plate, ranking, pause, title copyright, briefing page.
  - Width gate: `script/budgets.tsv` (rect + room; 228 rows can grow into their TIM), `tools/fit.py` (ok / grow / OVER, `tests/test_gfx.py` runs it on the spike). Subtitles: 288 px, two lines measured in game. Torture sheet `tools/torture.py`: all ASCII renders in every class; `|` is the line break.
  - Movies: `tools/mdec.py` + `tools/fmv_burn.py` ported from desu-yo (BOGO movies are STR v2 320x224, every frame roundtrips). STAFF.STR is v3: `tools/staff.py` decodes it with ffmpeg and writes v2 frames (`mdec.encode_rgb`) into the same sectors; **the game plays the v2 roll** (test line seen in `work/qa/spike/staff_roll`). Re-encoding all 2,415 frames takes ~20 min.
  - Review: independent `codex exec` (read-only) of the phase 5 code, `work/review/phase5_codex.txt`: ran the tests, 102 BPE round trips, rect isolation on 465 real rows, 5 STAFF frames rewritten in memory; 1 Minor (Bangers' italic overhang clipped by the glyph canvas, so the width gate measured 1 px short), fixed. In-game shots and font choices were read by the implementer only.
  - Encoder: `timp.bpe_best` (smallest of three block sizes) fixed a 2-byte growth the build test caught; limits measured from every disc block (15,623 bytes out, stack 78) in `docs/re/disc.md`.
- **Carried from phase 5 to 7:** left-align option for description panels; rect growth for `grow` rows after a zoomed look at their marker shot (neighbours overlap in machine data panels); briefing pieces (DOKURO#34-74) join at run time in an order set by code, unknown (the English assumes "First up:" + "<course>, y'hear"); briefing screen is 384 px wide mode.
- **Phase 4 (done 2026-11-14):**
  - `script/graphics.tsv`: 507 line rows over 453 text blobs (1,011 TIMs with text once copies are counted; `tools/gfx_index.py` names each blob by its first `ARCHIVE#entry`, the build replaces by hash). `script/no_text.txt`: the other 11,198 TIMs, as whole archives or entry ranges. `tests/test_script.py`: every TIM is in exactly one, rows name the canonical copy, every rect is inside its TIM and has ink. Forms: `keep` = the ボカン logo (D5), `fix` = SAVE#7 "CANSEL", `art` = lettering painted into a picture (RANK#81, SAVE#79/80, STAT#61), rect by eye.
  - Rects: one-line rows = the sprite's opaque box; multi-line panels from ink bands (`tools/gfx_sheet.py inklines`), split evenly where bands touch (noted), MSELECT plates by hand. Phase 5 should take exact spans in game. Draft source was `work/gfx/spec.tsv` (gitignored); from now on edit `graphics.tsv` itself (`gfx_script.py draft` would overwrite it).
  - Read: every unique GRAP menu blob at 2x, plus a half-size sweep of every other unique blob (GRAP art, all STAGE textures, CAR) with sign-like ones at 1.5x: no lettering outside the menus. Kanji in MODE1#1 line 2 (龍?) read small, flagged.
  - Save titles: `script/save_titles.tsv` (33), `tbl/save.tbl` (78 Shift-JIS chars), roundtrip-exact through `tbl.py` (test). The course list in them corrected two sprite readings (ゴッタガエシティー, もー大陸); ロ－スト uses a full-width minus there.
  - Movies: `script/fmv/BOGO01-18.tsv` cleaned, 292 dialogue rows with speakers. Two faster-whisper passes: `tools/fmv_transcribe.py` (whole movie, `work/fmv/BOGOxx.whisper.tsv`) and `tools/fmv_pass2.py` (each row's clip alone with a names prompt, `work/fmv/BOGOxx.pass2.tsv`), plus 2 s frame sheets (`work/fmv/BOGOxx/`) for speakers. Notes keep `was:`/pass-2 readings; 75 rows are `?` guesses. BOGO01 = 11 song rows with no text (D9: lyrics out of git). BOGO10 has no speech (the boss flower). Dropped rows (stock Whisper sign-offs, noise) and ear-check items are in `docs/polish.md`. Movie map: BOGO03-09 team movies, 11-17 team endings (Majo, Doronbow, Mujo, Atasha, Mirenjo, Munmun, Yanyan), 18 true ending; teams 0-6 in `docs/re/state.md`. No caption or sign text in any movie.
  - Credits: `script/credits.tsv`, 202 lines of STAFF.STR's roll (head/sub/name, cast as role groups + actor), read from 3 s frames at 2x (`work/fmv/STAFF/full/`). Uncertain glyphs noted per row and in `docs/polish.md`. The CG works line runs off the right edge in the original.
  - Review: independent `codex exec` (read-only) of every graphics crop (sheets from `gfx_script.py sheet`, which now prints each row's reading) and of the movie files + credits. Graphics: 40 findings, all checked zoomed and fixed (タイムラワーダ → タイムラクーダ x6, small ェ in DOKURO briefs x32, 、 in TUP0#73/74). Movies/credits: 23 findings; 13 fixed (三悪, 盲腸・小腸 gag, 苦よ来い, readings both passes agree on), restores of unreadable rows declined (listed in polish), 3 credit glyphs left as noted alternatives.
- **Still open from phase 1:** how DOKURO#34-74 briefing pieces are joined (order in code), which entries are tiled.
- **Done:**
  - Step 0: dump pinned (`rom.sha1`), pre-commit hook (`tools/hooks`), guard blocks `sed -i`, `tools/skill.py`, smoke boots the original disc on `tools/pcsx`. Not tested: GUI keyboard input (headless).
  - Phase 1: `docs/re/disc.md` (one data track, 197 TIMP archives = 12,197 TIMs, BPE at 0x800141AC, 19 STR movies, XA audio), `text.md` (no text engine; 33 Shift-JIS save titles in DEMO.BIN), `graphics.md` (every Japanese sprite by archive and entry). `tests/test_recon.py`.
  - Phase 2: `tools/debug/warp_all.py` reaches all **129 scenes** of `scenes.lua` from a cold boot with a shot each (`work/qa/warp/<scene>/final.png`); 114 end on a RAM check, the other 15 (story_save, ta/vs_courses, ta_ghost_loaded, 3 no-card, win_c0-7) only on their wait conditions and shots (no-card and card messages have no RAM flag found) ( 129/129 ok 2026-11-14, states regenerated in `work/states/`; contact sheets `work/qa/warp_sheet1.png`, `warp_sheet2.png`). Covers boot/title/menus, story (intro, machine select, 7 team movies, tune-up, warp, 8 briefings with every page shot, 8 races, 8 wins, boss losses, save, loss/retry, pause), GP/time attack/VS/ranking flows, options and every submenu page, movie viewer (all 19 movies), memory-card load/save and no-card messages, 7 team endings, true ending, staff roll, post-game save, game over. RE: `docs/re/state.md` (state table, race end per mode, endings, game over = M=0x11). `tools/mwrites.py` lists M writes.
  - Phase 3: `tools/build.py --identity` rebuilds every form 1 file (TIMP unpack/pack keeping each archive's word-aligned or packed layout, TIMs through pixels/with_pixels) and equals the dump; `tests/test_build.py` (identity sha1, an edited entry lands, write_file touches only its sectors).
- **Known limits:** headless PCSX-Redux needs RAM-only workarounds (`warp.lua`: SPU waits); `ending_entry`/`win_c7` end on the team ending movie that stalls headless when entered from the race (the same movies play in `ending_t*`). No code sets M=0x11 (game over) or M=0x23; `game_over` forces M=0x11 at dispatch. Phase 1 read course textures at half size and several archive families only as one sample. Phases 0-1 reviewed by the implementer only. Phases 2-3: independent `codex exec` review 2026-11-14, 5 findings, all fixed (identity test now proves every file is rewritten and all 196 TIMPs repacked, untouched entries keep their BPE bytes, `align_of` needs a real gap, `pack` asserts equal lengths, status wording on checks).
- **Open bugs:** none.
- **Waiting on the user:** all non-blocking agent defaults: D10 fonts per class (Bangers / Liberation Sans Bold / Jersey 10 / Tiny5; shots in `work/qa/spike2`); D7 burn English subtitles into BOGO02-18; D8 full-width English save titles; the ボカン logo stays Japanese (D5) unless an official English logo is found; English credits (D3) mean re-rendering STAFF.STR; D9 the opening song stays unsubtitled, lyrics out of git. Anyone who can listen: the movie rows in `docs/polish.md` (nobody has heard the audio).
