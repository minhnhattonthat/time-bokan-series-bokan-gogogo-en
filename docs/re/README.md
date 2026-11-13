# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [disc.md](disc.md) | disc layout, file types, TIMP archive format and BPE codec | verified except where marked |
| [text.md](text.md) | no text engine; the only Shift-JIS is 33 memory card titles in DEMO.BIN | verified by scan |
| [graphics.md](graphics.md) | graphics-text survey: every Japanese TIMP sprite, FMVs, staff roll | static sweep; in-game check in phase 2/8 |
