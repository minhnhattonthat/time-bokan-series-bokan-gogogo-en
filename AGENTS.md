# Time Bokan Series: Bokan GoGoGo (PS1) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `python tools/skill.py` prints its folder; `$SKILL` = that folder). Read its SKILL.md before ROM, text or QA work. Sibling project for reuse: `../time-bokan-series-bokan-desu-yo-en` (disc, TIM, FMV subtitle tools).

## Commands (run from repo root)
- Hooks:    `git config core.hooksPath tools/hooks` (once per clone)
- Check:    `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this)
- Dump:     `python -X utf8 tools/check_rom.py` (checks the dump against `rom.sha1`)
- Extract:  `python -X utf8 tools/disc.py x "rom/Time Bokan Series - Bokan GoGoGo (Japan).bin" work/x`; TIMP archives: `tools/timp.py list|x`
- Survey:   `python -X utf8 tools/tmp_sheets.py work/recon/grap work/x/GRAP/*.TMP` (each archive's entries, labelled); `tools/str_frames.py BIN work/recon/str --every 3` (FMV samples)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py "rom/Time Bokan Series - Bokan GoGoGo (Japan).cue" --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 tools/debug/warp_all.py [--jobs 6] [--states] [scene ...]` (cold boot to a scene by name, shot in `work/qa/warp/<scene>/final.png`; `--list` names all; `--states` regenerates `work/states/`). Scenes and their RAM writes: `tools/debug/scenes.lua`. Card fixtures (game-written): `work/qa/warp/story_saved/memcard1.mcd`, `work/qa/warp/ta_ghost_save/memcard1.mcd` (`--sav`).
- Build / Release: not written yet (phases 3, 9).
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original disc: `rom/` (gitignored; one MODE2 track .bin + .cue, SHA-1s in `rom.sha1`). Emulator: this repo's own PCSX-Redux in `tools/pcsx/` (gitignored). BIOS: `tools/bios/scph5500.bin`. Savestates: `work/states/`.
- Text: no text engine; strings are TIM sprites in TIMP archives, movie frames, and 33 save titles. Survey: `docs/re/graphics.md`. Glossary: `glossary.md`. RE notes: `docs/re/README.md`. Fonts: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose. In an Orca one-shot run nested workers are refused: do reviews yourself in a fresh read-only pass, or with `codex exec`.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Gotchas: Japanese games confirm with circle. Text sprites repeat across archives (STAT x40, TUP x7, names in 6+ files): replace by blob hash everywhere. Some TIMs have a wrong pixel-length word: `tim.parse(b, strict=False)`. `disc.write_file` keeps LBAs, so a grown TIMP file needs free sectors after it.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
