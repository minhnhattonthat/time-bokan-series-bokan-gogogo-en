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
