# Visual-QA reviewer brief - Time Bokan Series: Bokan GoGoGo (PS1)

You review contact sheets from the English build's warp tour and give each one a verdict. Read-only on everything
except your one verdict file (or, under `codex exec` read-only, print the verdict lines as your final answer and the
controller saves them): no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped. The id is the warp
  scene name (`tools/debug/scenes.lua`); `-2`, `-3` are further pages of the same scene.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- The original disc's sheet of the same scene: `work/qa/sheets_jp/<id>.png` (same warp, Japanese).
- `glossary.md` for names. The game has no text engine: every word on screen is a sprite (TIM) lettered by
  `tools/gfx.py`, a subtitle burnt into a movie (BOGO02-18), or the re-lettered STAFF.STR credits roll.

## How to look
- Read each sheet whole first. Each tile is one warp shot at full size (320 or 384 px wide). Where text is small,
  zoom: `python -X utf8 $SKILL/scripts/sheet.py SHOT.png --crop x,y,w,h --zoom 3 --out <scratch>.png` on the shot
  named under the tile (`work/qa/env/<scene>/<shot>.png`).
- When something looks wrong, compare with the Japanese sheet. Same layout/behaviour there = the game's own: `ok`.
- Menus, buttons, plates and panels: is the English inside its plate or panel, clear of the border and of
  neighbouring sprites, and centred where the Japanese was centred?

## Judge
An `issue` is any of:
- Japanese still visible (except the standing non-bugs below);
- text overflowing a plate, panel or button, clipped by a frame, overlapping a neighbouring sprite, or off screen;
- text off-centre where the original centres it;
- garbage pixels, missing or wrong glyphs, a strike or stray Japanese ink (dakuten, a stroke tail) beside English;
- broken line breaks in a panel or subtitle (a word split, one-word last line);
- an empty plate or panel where text belongs;
- a name that differs from `glossary.md`;
- unreadable text: outline swallowing the letters, ink the same colour as its background.

Standing non-bugs (`ok`):
- the ボカン / タイムボカンシリーズ logo stays Japanese (decision D5);
- a fade, a flat-colour frame or a loading screen right after a warp; `ending_entry` ends on a flat frame by design;
- scenes forced by the warp (e.g. `game_over`, a race already won) showing a combination normal play reaches
  differently: judge only the text;
- the opening song (BOGO01) and the boss flower movie (BOGO10) have no subtitles (D9, no speech);
- course textures, signs in 3D races and numbers/times drawn by the game: not lettering we changed;
- the narrow class (Tiny5 drawn twice as tall, decisions D11/D14) in the 40 px movie tabs and the character name
  plates: thin and condensed by design, as no wider font fits; `issue` only if a letter can't be told apart in a 3x
  zoom of the shot, or the colours/outline make it unreadable;
- anything identical in the Japanese sheet except the Japanese text itself.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
