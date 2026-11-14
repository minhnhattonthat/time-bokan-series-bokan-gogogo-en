# Time Bokan Series: Bokan GoGoGo English translation

Unofficial English fan translation of **Time Bokan Series: Bokan GoGoGo** (PlayStation, Banpresto, 2001): the source
text and tools that build the patch. Progress and open bugs are in `docs/status.md`.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Movie dialogue | English subtitles burned into the story movies; voices stay Japanese |
| Menus, options, HUD | Translated |
| Course, machine and character names | Translated (all lettering is drawn as graphics in this game) |
| Dokurobey's briefings | Translated |
| Credits roll | Translated, re-lettered in the staff roll movie |
| Memory card save titles | English (full-width, as the original's) |
| Title logo | Left in Japanese, as no official English logo is known |
| Opening song | Not subtitled, as in the original |
| Songs and voices | Left in Japanese |

Known issues: nobody checked the subtitles by ear, as they come from machine transcription with corrections, and a few
short lines on unclear audio have no subtitle; "Andromedama" and "Whyzca" are shortened on the sprites; some credit name
readings are unconfirmed. Tested on PCSX-Redux only, by scripted warps to every scene rather than a full playthrough.
See also [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched disc

Needs Python 3.12+, ffmpeg (credits roll) and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/time-bokan-series-bokan-gogogo-en
cd time-bokan-series-bokan-gogogo-en
# copy your dump (.bin and .cue, one data track) to rom/:
#   rom/Time Bokan Series - Bokan GoGoGo (Japan).bin
#   (651616896 bytes, CRC32 2f7887fb, MD5 4154783b236d9c2f70355832f720887b,
#    SHA-1 c3517ef78e4724c929c9b55025faf68cafcf39f4; the build refuses any other dump, see rom.sha1)
# Redump: http://redump.org/discs/quicksearch/SLPS-03133/
python -X utf8 tools/staff.py decode "rom/Time Bokan Series - Bokan GoGoGo (Japan).bin" work/fmv/STAFF/all
python -X utf8 tools/build.py --en                     # -> build/en/ (about 30 min with the credits roll)
python -X utf8 tools/check.py                          # tests + text lint
python -X utf8 tools/release.py 1.0                    # QA gates, xdelta patch, re-apply check, zip in release/
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Banpresto's and is included only so
the translation can be checked against it. Time Bokan Series: Bokan GoGoGo is (c) Banpresto and Tatsunoko Production;
this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
