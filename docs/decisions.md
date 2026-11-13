# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

D1-D3, D5, D6 are the owner's standing answers for one-shot runs; D4 is the skill default. D7+ are agent defaults the
owner can overrule. Per-game override: the bokan-desu-yo-en project may be used as reference.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-13 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western name order. Owner's standing answer. |
| D2 | 2026-11-13 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. Owner's standing answer. Names follow desu-yo's glossary, checked on Tatsunoko's English site. |
| D3 | 2026-11-13 | Credits | stay Japanese, translate | English. Owner's standing answer. Here the credits are a movie (STAFF.STR), so this needs that movie re-rendered. |
| D4 | 2026-11-13 | Abbreviations | engine work first (default), abbreviate | Engine work first; abbreviate only as a flagged last resort. Skill default. |
| D5 | 2026-11-13 | Graphics text left in Japanese | none (default), list | Translate all of it. The ボカン / タイムボカンシリーズ logo stays only if no official English logo exists. Owner's standing answer. |
| D6 | 2026-11-13 | Specs and plans | need approval, pre-approved | Pre-approved. Owner's standing answer. |
| D7 | 2026-11-13 | Spoken story in BOGO02-18 (no subtitles) | leave; burn English subtitles | Burn in subtitles, reusing desu-yo's `mdec.py`/`fmv_burn.py`, if each movie keeps its sector count. **Agent default**, as in desu-yo: the story is otherwise lost. |
| D8 | 2026-11-13 | Memory card save titles (Shift-JIS, BIOS manager only) | leave; full-width English | Full-width English, same byte length. **Agent default.** |
| D9 | 2026-11-14 | Opening song (BOGO01) lyrics | subtitle them; leave unsubtitled | No subtitles (the original shows none) and verbatim lyrics stay out of git, as third-party text: `script/fmv/BOGO01.tsv` keeps only the song rows' times, the readings live in gitignored `work/fmv/BOGO01.*.tsv`. Same as desu-yo D8. **Agent default.** |
| D10 | 2026-11-14 | Fonts per label class (graphics rows, FMV subtitles) | one font throughout; a font per class, as desu-yo | A font per class, taking desu-yo's owner rulings as the precedent, picked by lettering candidates into the real TIMs side by side with the Japanese (`tools/font_try.py`) and checked in game on `build.py --spike`: Bangers only at 22 px and up (`title` 34, `big` 28, `menu` 22 with a light inner and dark outer outline like the mode-select art), Liberation Sans Bold 14 with a 1 px outline for small buttons and bars (`bar`, desu-yo D16), Jersey 10 at its native 18.67 px (desu-yo D14) with the double outline for names, courses, machines, stats, messages and briefings (`sign`), plain for description panels and team names (`label`), Tiny5 at its native 8 px for 8-10 px rows (`small`), FMV subtitles in Liberation Serif Bold 13 px on a soft halo (desu-yo D15). Map: `CLASSES`/`FORM_CLASS` in `tools/gfx.py`; licences in `docs/fonts.md`. **Agent default.** |
| D11 | 2026-11-14 | Names and words that overflow their sprite in every D10 class (character names in 24-64 px plates, movie tabs, a few song titles, スカ, 逆走行) | abbreviate; a narrow class | A narrow class: Tiny5 drawn twice as tall (`narrow` with one outline, `narrowlabel` plain), ~4 px a letter at cap 10, so Tanpei fits the 24 px of 丹平. Single rows that are 1-4 px over in their form's class take `label` (Zenderman cup plate, Denden Mecha, Mechabuton, Time Mechabuton, two song titles). Course names were re-punned to fit instead (glossary). Machine-select plates in caps. **Agent default**; phase 8 judges the look in game. |
| D12 | 2026-11-14 | Dokurobey's tic, honorifics, Top Billing | ", y'hear" / ", bey" / none; -sama / Lady, Lord; Top Billing / Starring Seat | Tic ", y'hear" and 様 as "-sama" follow desu-yo (same series; D1 keeps honorifics). 主役の座 (the flower, cup and boss) = "Top Billing", so his promise of 主役 reads "top billing in the new world". **Agent default.** |
