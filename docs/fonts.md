# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release. Classes and sizes: `CLASSES` in `tools/gfx.py`, D10.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `fonts/Bangers-Regular.ttf` | Google Fonts (Vernon Adams), via the desu-yo project | OFL 1.1 (`bangers.OFL.txt`) | yes, as rendered pixels | classes `title`, `big`: screen titles, art lettering, race HUD words | - |
| `fonts/Jersey10-Regular.ttf` | Google Fonts (Sarah Cadigan-Fried), via desu-yo | OFL 1.1 (`jersey10.OFL.txt`) | yes | class `label` at its native 18.67 px: names, courses, machines, messages, briefings, panels | - |
| `fonts/Jersey15-Regular.ttf` | Google Fonts, via desu-yo | OFL 1.1 (`jersey15.OFL.txt`) | yes | the phase 5 STAFF.STR spike line only (`tools/staff.py spike`); class `credit` is unused in `graphics_en.tsv` | - |
| `fonts/LiberationSans-Bold.ttf` | Liberation Fonts 2.x, via desu-yo | OFL 1.1 (`LICENSE-Liberation.txt`) | yes | class `bar`: buttons, menu bars, cups, laps, teams; the STAFF.STR credits roll at 12 px (`tools/staff_roll.py`, D13) | - |
| `fonts/LiberationSerif-Bold.ttf` | Liberation Fonts 2.x, via desu-yo | OFL 1.1 (`LICENSE-Liberation.txt`) | yes | FMV subtitles (`tools/fmv_burn.py`, desu-yo D15 style) | - |
| `fonts/Tiny5.ttf` | github.com/Gissio/font_tiny5, via the nage-libre project | OFL 1.1 (`tiny5.OFL.txt`) | yes | class `small` at its native 8 px: 8-10 px rows (copyright line) | - |
