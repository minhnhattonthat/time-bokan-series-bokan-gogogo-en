# Polish

Open items that are not bugs: things a person should check by ear or eye before release. Tick a line when it is done.

## Movies: listen to these (phase 4, nobody has heard the audio)

Transcripts are two faster-whisper large-v3 passes (`tools/fmv_transcribe.py`, `tools/fmv_pass2.py`), cleaned from
frame sheets, franchise knowledge and context. Rows whose note starts with `?` are guesses (text or speaker):
75 of 292 dialogue rows. An independent `codex exec` read (2026-11-14) fixed 13; the rows it wanted restored with
no usable reading stay dropped and are listed below. `grep -P '\t\?' script/fmv/*.tsv` lists them.

- [ ] BOGO02-18: every `?` row.
- [ ] Rows dropped as unclear or invented (pass-1 text, start time). Check none is real speech:
  BOGO04 30.32 あああ; BOGO06 3.14 アントロメダマゴアルファ, 27.74 ぴょーん!, 28.40 おちゃむー!; BOGO09 25.90 にゅー!;
  BOGO10 7.72 (stock Whisper sign-off over the boss reveal; no speaker on screen); BOGO11 79.94 そうやな (pass 2
  さようならー!); BOGO12 28.90 なあ?, 38.62 どう?…, 54.50 わー!, 55.36 えい!, 56.16 なんでだ!, 57.30, 60.96, 62.20
  (scramble for the flower), 83.46; BOGO13 88.14 玉ー; BOGO14 78.78 えぇ!?, 108.78-113.84 (noise
  over the ship), 135.66 (stock sign-off); BOGO15 59.00 何だ!, 60.22 マジー!, 88.80 知らん; BOGO16 54.92, 116.22 はい!;
  BOGO17 38.34 うめ。; BOGO18 10.56 もや?, 31.46-52.02 (rocket and explosion, pass 2 gives stock sign-offs).
- [ ] BOGO01 8.92 はぁっ!? (a shout at the logo flash?) was dropped with the invented 作詞・作曲 row.
- [ ] Names Whisper never got right: BOGO14's comet (大空/大ブラ/オボラ 大彗星, written 大ボラ), BOGO15 キョウシー
  (written ジュリー), BOGO13 ドクメ (written ドクロベエ), BOGO15 ナンダラ王国 / コマロ.
- [ ] BOGO12 91.76: who goes back to "my original form", Dokurobey or the gang (frames 76-96 s).

## Translation (phase 6): cuts and font overrides to look at in game

- [ ] CUT: アンドロメダマ号α is "Andromedama" on sprites (no α glyph; "Alpha" is 1-8 px over on the plate and SAVE#42).
  Subtitles keep "Andromedama Alpha". Phase 7: a hand-drawn α, or a rect grown after a zoomed look.
- [ ] CUT: ナゼカ平原 is "Whyzca" (平原 dropped; "Whyzca Plain" is 87 px in 80 px sprites).
- [ ] Class overrides that mix fonts inside one list (D11): songs MODE#35 (`label`), MODE#38/41 (`narrowlabel`), MODE#14/15
  (`label`), machines MODE#96/105 and copies, CSELECT#87 (`label`), cup plate CSELECT#2.1 (`label`). Check the look.
- [ ] SAVE#7: only "CANSEL" is relettered as "CANCEL" in Liberation Sans Bold; copying the sprite's own C over the S
  would keep the italic art (phase 7).
- [ ] シュウリョウ movie tab read as "Finish" (tabs run Opening, Dokurobey, Start, Finish, Ending, Punishment: likely
  BOGO10, the boss reveal); check which movies it lists in the movie viewer.
- [ ] Names Whisper guessed now have English (BOGO15 Julie / Komaro / Nandara, BOGO14 comet): same ear check as above.

## Credits

- [ ] `script/credits.tsv` readings marked in the note (ヒエール on screen vs the ピエール sprite, 尾鼻, セルシェーダー
  (codex read セルシューター)): check against a staff list or a sharper frame. Settled in the phase 6 review from
  published credits: 栫 久美子 Kumiko Kakoi (was read 椿/梅), プローバワークス Prova Works, 鉄羅 紀明 Toshiaki Tetsura,
  石渡 利明 Toshiaki Ishiwatari, スタジオ・アド Studio Add. Other name readings are Hepburn guesses from the kanji.
