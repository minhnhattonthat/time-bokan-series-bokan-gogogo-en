# Polish

Open items that are not bugs: things a person should check by ear or eye before release. Tick a line when it is done
(`[x]` fixed, or `waived: reason`). The release script refuses to run while any line is unticked.

## Movies: listen to these (phase 4, nobody has heard the audio)

Transcripts are two faster-whisper large-v3 passes (`tools/fmv_transcribe.py`, `tools/fmv_pass2.py`), cleaned from
frame sheets, franchise knowledge and context. Rows whose note starts with `?` are guesses (text or speaker):
75 of 292 dialogue rows. An independent `codex exec` read (2026-11-14) fixed 13; the rows it wanted restored with
no usable reading stay dropped and are listed below. `grep -P '\t\?' script/fmv/*.tsv` lists them.

- [x] BOGO02-18: every `?` row. waived: no listener in this run (the agents can't hear audio); two Whisper passes,
  frame sheets and three codex reads agree on them, and the phase 9 story pass (`work/qa/story`) read every chapter
  in order and found them coherent. Listed in the README's known issues; a listener's corrections are welcome.
- [x] Rows dropped as unclear or invented (pass-1 text, start time). waived: same as above; all are cries, noise or
  Whisper's stock sign-offs over music, none carries plot (the story pass found no gap):
  BOGO04 30.32 あああ; BOGO06 3.14 アントロメダマゴアルファ, 27.74 ぴょーん!, 28.40 おちゃむー!; BOGO09 25.90 にゅー!;
  BOGO10 7.72 (stock Whisper sign-off over the boss reveal; no speaker on screen); BOGO11 79.94 そうやな (pass 2
  さようならー!); BOGO12 28.90 なあ?, 38.62 どう?…, 54.50 わー!, 55.36 えい!, 56.16 なんでだ!, 57.30, 60.96, 62.20
  (scramble for the flower), 83.46; BOGO13 88.14 玉ー; BOGO14 78.78 えぇ!?, 108.78-113.84 (noise
  over the ship), 135.66 (stock sign-off); BOGO15 59.00 何だ!, 60.22 マジー!, 88.80 知らん; BOGO16 54.92, 116.22 はい!;
  BOGO17 38.34 うめ。; BOGO18 10.56 もや?, 31.46-52.02 (rocket and explosion, pass 2 gives stock sign-offs).
- [x] BOGO01 8.92 はぁっ!? (a shout at the logo flash?) was dropped with the invented 作詞・作曲 row. waived: BOGO01
  carries no subtitles at all (D9).
- [x] Names Whisper never got right: BOGO14's comet (大空/大ブラ/オボラ 大彗星, written 大ボラ), BOGO15 キョウシー
  (written ジュリー), BOGO13 ドクメ (written ドクロベエ), BOGO15 ナンダラ王国 / コマロ. waived: best readings from
  context and the shows' casts (Julie Kokematsu is Yattodetaman's; Dokurobey speaks in BOGO13); README known issue.
- [x] BOGO12 91.76: who goes back to "my original form", Dokurobey or the gang (frames 76-96 s). waived: the line reads
  right for either speaker in the story pass (02_doronbow ok); the speaker column is a guess, not shown on screen.

## Translation (phase 6): cuts and font overrides to look at in game

- [x] CUT: アンドロメダマ号α is "Andromedama" on sprites (no α glyph; "Alpha" is 1-8 px over on the plate and SAVE#42).
  Subtitles keep "Andromedama Alpha". waived: Jersey 10 and Bangers have no α (checked with fontTools), a hand-drawn
  glyph in five sprites for one suffix isn't worth the risk; the movies give the full name (D4, flagged cut).
- [x] CUT: ナゼカ平原 is "Whyzca" (平原 dropped; "Whyzca Plain" is 87 px in 80 px sprites). waived: the pun is the name;
  the place is clear from the course itself (D4, flagged cut).
- [x] Class overrides that mix fonts inside one list (D11): songs MODE#35 (`label`), MODE#38/41 (`narrowlabel`),
  MODE#14/15 (`label`), machines MODE#96/105 and copies, CSELECT#87 (`label`), cup plate CSELECT#2.1 (`label`). Checked
  in game: every sheet showing them got an `ok` verdict in phase 8 (build 6642505a, `work/qa/verdicts`).
- [x] SAVE#7: only "CANSEL" is relettered as "CANCEL" in Liberation Sans Bold. Checked in game: the save sheets got
  `ok` verdicts in phase 8; the mix of italic art and the relettered word was not flagged.
- [x] シュウリョウ movie tab read as "Finish". waived: 終了 means finish/end, so "Finish" is the literal tab name
  whichever movie it lists; the tab sits between Start and Ending like the Japanese.
- [x] Names Whisper guessed now have English (BOGO15 Julie / Komaro / Nandara, BOGO14 comet): waived with the names line
  above.

## Credits

- [x] `script/credits.tsv` readings marked in the note: checked against MobyGames' credits for this game (2026-11-14):
  ヒエール is right (Kiramekiman's Hierre; "Pierre" was wrong, fixed in the credits and the MODE#177 sprite),
  セルシェーダー = Cel Shader, 尾鼻 直人 Naoto Obana, 中嶌 隆史 Takashi Nakajima, Prova Works confirmed;
  角田 恵子 now Keiko Kakuta and 岡本 茉利 (the voice actress) as MobyGames gives them. Settled in phase 6 from published
  credits: 栫 久美子 Kumiko Kakoi, 鉄羅 紀明 Toshiaki Tetsura, 石渡 利明 Toshiaki Ishiwatari, スタジオ・アド Studio Add.

## Story pass (phase 9)

- [x] BOGO02 continuation lines start with "..."; BOGO12@85.64, BOGO13@69.94, BOGO06@18.76, BOGO07@12.64, BOGO18@1.34,
  BOGO14@45.84 reworded (codex story-pass Minors, `work/review/phase9_story_fixes*.tsv`).
- [x] BOGO06@21.28 "I'll take another bowl, too!" (いただく echo): kept, the suggestion was this same line.
