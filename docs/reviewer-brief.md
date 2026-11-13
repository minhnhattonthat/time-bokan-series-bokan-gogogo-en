# Translation reviewer brief - Time Bokan Series: Bokan GoGoGo (PS1)

You review one batch of a JP->`English` fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, control codes, encodable characters, width, stub last lines) is already enforced by the
check tool - judge translation quality. Return the report as your final message: subagents cannot write files, so the
controller saves it.

## Inputs (paths in your dispatch)
- Pairs file: every translated entry as `>> id | JP` / `EN` with +-2 context lines. Read ALL of it, in passes if large.
- `glossary.md` (rulings at the top), `docs/style-reference.md`, the translator's report (unverified claims).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly (a one-letter slip like "Bran" for "Plan" is what players notice); honorific relationships stable
  within a scene; voice matches the style reference.
- Things players and users caught that reviewers missed: jokes/wordplay losing their punch; ordinal suffix after a
  variable ("1th"); abbreviated names or terms (unless the glossary rulings allow them); stock phrases that read awkwardly in English ("... GET!").
- Voice: each speaker against their row in the style reference. Speech quirks (〜っス, 〜ぞい, 〜ニャ, ござる, drawn-out
  〜ぉ/〜ぅ endings, katakana robot speech), register (a king's formality, a thug's swagger, a child's cuteness) and
  emotional intensity (rage, fear, comic timing) must come through in English, not be normalised into neutral prose.
  Register markers flatten most often, more than quirks: old-man じゃ/のう/わし, rough ぜ/ねぇ/っス, feminine
  かしら/わよ/のね. Audits of two patches found about 9 in 10 old-man lines and nearly every かしら line turned neutral.
- Naturalness: would a fan-translation reader stumble? Against the glossary's Style rules: register and voice per
  scene, calques of an earlier translation (a second-language pass copies English phrasing).

## Report
### Issues
#### Critical (meaning reversed, broken placeholder grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a character's voice flattened: quirk, register or emotional beat lost, joke dead)
#### Minor (style - these are deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.

## This game
- Pairs files from `tools/pairs.py OUT`: `gfx.txt` (unique graphics strings; the form/class and the sprite size in px
  tell you how little room there is: a fix must not be longer unless you say so), `fmv.txt` (every movie row in story
  order, so it is its own context; notes give the Whisper uncertainty), `credits.txt`, `save.txt` (full-width
  card titles).
- Graphics widths are already gated by `tools/fit.py`; flag meaning and naming, and say when a shorter word would do.
- Briefing sprites (`brief`, DOKURO#34-74) are pieces the game joins at run time in an order set by code (unknown):
  "First up:" + "<course>, y'hear", "Top 3..." + "you didn't make it, y'hear!".
