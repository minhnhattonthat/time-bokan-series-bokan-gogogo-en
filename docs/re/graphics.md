# Graphics-text survey

Every Japanese string the player sees is pixels in a TIM inside a TIMP archive (`docs/re/disc.md`), a frame of an STR
movie, or the 32 memory-card save titles in `OVER/DEMO.BIN` (`docs/re/text.md`). Ids are `ARCHIVE#entry`, entry =
index in `tools/timp.py list`. Sheets: `python -X utf8 tools/tmp_sheets.py work/recon/grap work/x/GRAP/*.TMP`.

**Phase 4: `script/graphics.tsv` is now the authority** (453 text blobs, 507 line rows, read at 2x with
`tools/gfx_sheet.py`); this file is the phase 1 sweep. Corrections found then: the course is ゴッタガエシティー (not
ブッタ), もー大陸 (not も一), as the Shift-JIS save titles spell them; MODE #90-105 and #149-182 were off by one or two
here; MODE1#3 is the same blob as MODE#0; STAT #61 is the スカ (dud) item icon; MSELECT #25's team is 怪盗きらめきマン.
Copies: 1,011 TIMs carry text, 453 distinct blobs (`tools/gfx_index.py`, canonical = first id in sorted order).
A second sweep of every unique non-menu blob (`work/gfx/grapart_*`, `stage_*`, `car_*` at half size, sign-like
textures at 1.5x) found no lettering in CAR, STAGE courses or the GRAP art archives.

Read from contact sheets at 1x (clut 0). **Static sweep only:** which entries show, and where, is for phase 2/5 to
confirm. "label" = a single word/phrase sprite; "panel" = a picture with lettering inside.

## GRAP/TITLE.TMP (43 entries) - title screen
- #5, #6, #16 and #7-15 (logo pieces): ボカン, タイムボカンシリーズ logo. Logo: stays Japanese unless an official English
  logo exists (D5). #4 "GO" is English.
- #29 copyright: (C)タツノコプロ 2001 / (C)タツノコプロ・テレビ東京 / (C)BANPRESTO 2001 -> romanize "Tatsunoko Pro", "TV Tokyo".
- #30 スタート, #31 ロード. (#28 PRESS START BUTTON, #33-42 digits: English already.)

## GRAP/MODE.TMP (204 entries) - mode select, options, story mode, machine data, movie list
- #0 caption box: タイムボカンに登場 / 時間航行可能な / 栄光の悪玉1号マシン (3-line description panel).
- #1 モード セレクト (big title). #2 ストーリーモード #3 GPモード #4 VSモード #5 タイムアタックモード #6 オプション #8 ランキング.
- #9 プレイ セレクト (title). #14 それゆけガイコッツ #15 天才ドロンボー (story team names? confirm). #16 ミュージック #17 オプション (titles).
- #18 コントローラ #19 マシンデータ #20 ミュージック #21 ムービー #22 もどる (options menu).
- #27-44 song titles (music player): シビビーン・ラプリディー, とびびぃ~んセレナーデ, 空からブタが降ってくる, ドロンボーのシラーケッ,
  ボカンと一発!ドロンボー, これまたアクダマン, ヤッターマンの歌, アーウー・オジャママン, ゼンダマンの歌, ヤットデタマン・ブギウギ・レディ,
  オタスケマンの歌, ヤットデタマンの歌, チュウ・チュウ・チャン, タイムボカン, 逆転イッパツマン, いただきマンボ. #43/#44 コントローラ 1 / 2.
- #45 コントローラ (title). #46-48 タイプA/B/C, #49 もどる, #50 バイブレーション (#51 ON, #52 OFF English).
- #67-72 アクセル ハンドル ブレーキ ドリフト アイテム バック (button config).
- #73 ストーリーモード (title). #74 さいしょから #75 つづきから.
- #76-88 story picture cards: art only (no lettering seen at 1x).
- #89 マシン データ (title). #90-#105 machine names (タイムガイコッツ, ドロンボータンク, シャレコウベメカ, シャレコウベバギー,
  アンドロメダマ号α, タイムラクーダ, デンデンメカ, ヤッターワン, ゼンダライオン, ワンダーブル, トッタルニャン, メカブトン ...), #97 もどる.
- #98 スピード #99 ダッシュ #100 グリップ (stat labels).
- #115-126 team names: マージョ一味, ドロンボー一味, アクダマン, オジャママン, ミレンジョー一味, クリーン悪トリオ, ヤンヤンシー行,
  ヤッターマン, ゼンダマン, 花の刑事(デカ)トリオ, きらめきマン, タイムボカン.
- #139 ムービー (title). #140-145 movie list buttons: オープニング, ドクロベエ, スタート, シュウリョウ, エンディング, おしおき.
- #146-148 全悪共通 (badge). #149-182 character names (マージョ, ワルサー, ムージョ, スカドン, コケマツ, グロッキー, トンズラー, ドロンジョ,
  ボヤッキー, ドンジューロー, トボッケー, ドワルスキー, アターシャ, セコビッチ, ミレンジョ, キョカンチン, コスイネン, ムンムン, トンメンタン,
  マンマン, ダサイネン, ヤッターマン1号/2号, ゼンダマン1号/2号, 丹平, 淳子, ルージュ, ヒエール, オンドレー, きらめきマン1号/2号 ...).
- #183-198 course names (16 + クタビレゾンの森2). #202 マシン #203 クリアコース.

## GRAP/CSELECT.TMP (123 entries) - course select, GP select, lap count, time records
- #0-7 グランプリ cup buttons: タイムボカン, ヤッターマン, ゼンダマン, オタスケマン, ヤットデタマン, イッパツマン, イタダキマン, シュヤクノザ.
- #25-41 course names (other font, 17 incl. クタビレゾンの森2). #42/#43 ワンダーブル, トッタルニャン.
- #61 コース セレクト (title). #62 コースを4つ選んで下さい! #63 コースを選んで下さい!
- #67 panel ラップ1/2/3, #68 周回数? #69-77 ラップ1-9.
- #78-86 machine names (タイムガイコッツ ... ゼンダライオン), #87 タイムメカブトン.
- #112 ベストタイム #113 ベストラップ. #119 このグランプリでよろしいですか? #120 はい #121 いいえ.

## GRAP/MSELECT.TMP (34 entries) - machine select
- #2 マシン セレクト (title). #13-25 two-line machine/team plates (machine name over team name, 13 plates, #13 highlighted).
- #31 ゴーストをロードしますか? #32 はい #33 いいえ. (#26/#27 1P/2P English.)

## GRAP/RANK.TMP (83 entries) - time-attack ranking
- #0 ランキング (title), #1 menu panel: レコードをセーブする / ゴーストをセーブする / リトライ / コースチェンジ / マシンチェンジ / ゲームをやめる.
- #3-14 machine names (12), #46-61 course names (16). #78 ベストタイム #79 ベストラップ.
- #81 background art with ランキング lettered in. (#15-33 digits, 1st-7th English.)

## GRAP/RESULT.TMP (82 entries) - race result
- #1 レース結果 (title). #4-7 リトライ コースチェンジ マシンチェンジ ゲームをやめる. #8 ランク・イン #9 レコードを記録する.
- #10-21 machine names, #53-68 course names. #69 総合結果. #72-80 ラップ1-9, #81 トータルタイム. (Win/Lose, 1st-7th English.)

## GRAP/SAVE.TMP (93 entries) - memory card load/save
- #0-37 memory-card messages, one sprite each (スロット 1/2, 使用するスロットを選んで下さい。, メモリーカードをチェックしています。, ...
  ゴーストデータがこわれています。); #7 "OK" / "CANSEL" button legend (English but misspelt: fix to CANCEL).
- #39-51 machine names (#46 ????????, locked), #52-68 course names (17). #69-72 ファイル1-4, #73 マシン #74 クリアコース #75 コース.
- #79 ロード, #80 セーブ (big lettered panels). #83 はい #84 いいえ. (#85 LAPTIME English.)
- #76-78 art (monitor, Dokurobee/character): no lettering seen.

## GRAP/DOKURO.TMP (87 entries) - story mode: Dokurobee's briefing and race result
- #1 レース結果. #3-9 machine names. #34-74 Dokurobee message pieces, assembled into sentences at run time: はじめのコースは、 /
  つぎのコースは、 / 3位までに、ゴールするだベエ~ / 1位で、ゴールするだベエ~ / <course> だベエ~ (16) / シュヤクノザを、倒すだベエ~ /
  よくやったベエ / ステージクリアだベエ~ / おめえたち / がんばるだベエ~ / <rival machine>に勝つだベエ~ (8: メカブトン, ヤッターワン,
  ゼンダライオン, 弾丸ヘッド号, 巨神号, カブトゼミ, オタスケタヌキ) / セーブしますか? / ゲームを終了しますか? / はい / いいえ /
  3位までに、ゴールできなかったベエ~ / 1位に、なれなかったベエ~ / もう一度、がんばるだベエ~ / いよいよ 勝てなかったベエ~.
  Joining order is code: phase 2/5 must find how pieces are placed (English word order differs).
- #75 ドクロストーン獲得数 #76 チューンアップポイント. (#86 Dokurobee portrait, art.)

## GRAP/TUP0-6.TMP (76 entries each) - tune-up shop (story mode)
Entries 0-37 and 57-75 are byte-identical in all 7 files (`tools/timp.py`); 38-56 (team portraits, machine turns) differ.
- #1 チューンアップ (title). #3 スピード #4 ダッシュ #5 グリップ #6 終了. #22 PTS. (English).
- #57-72 course names, #73 次のコースは。 #74 はじめのコースは。 (small font). #75 speech balloon (blank).

## GRAP/MODE1.TMP (12 plain TIMs back to back, not TIMP) - machine description panels
- #0-11 three-line descriptions, one per machine (オタスケマンに登場 / 小型走行用に新開発の / スーパービッグマシン, ...). Same style as
  MODE#0, which is the 13th panel.

## GRAP/GOVER.TMP (9) - game over
- #8 ゲームオーバー. Rest is art.

## No lettering seen (read at 1x unless noted)
- LOGO (Banpresto, English), WIN (team victory portraits), WIN1-5, LOST0-7 (losing teams, LOST0/3/7 read, rest same
  layout), BOS0-7 (boss course art, BOS0/7 read), SETU0-7 (story art, SETU0/1/4/7 read at 2/3), COK_* (cockpit frames,
  COK_GAI read), RESULT01-16 (one course backdrop each, RESULT01 read), WARP.
- CAR/: ANDRO, F_AKU0 (face icons), CAR_M0, CAR1P_00, CAR read; the other CAR files are the same kinds per team.
- STAGE/CORCE01-16, CORCE15B, BOSS00-07: track textures read at about half size, no lettering; COS_GP01 read at 1x.
  The phase 2 tour of every course confirms this in game.

## STAGE/STAT*.TMP (40 files, 188-199 entries) - race HUD and pause menu
Every text entry below is byte-identical in all 40 files (and #31/#193 appear twice in each).
- #30 ゴール #31/#193 ファイナルラップ #97 逆走行 (wrong way). Pause: #93 リスタート #94 GPのはじめに戻る #95 モードセレクトに戻る
  #96 タイトルに戻る #102 ゲームに戻る. (#32/#33/#194/#195 Win/Lose, #92 PAUSE, LAP, LAPTIME, TIME, FRONT/BACK: English.)
- #61 small red badge with kana (read zoomed in phase 4).

## Movies (STR, 320x224) - sampled every 3 s (`work/recon/str`, sheets `work/recon/fmv_00-07.png`)
- BOGO01 opening: TIME BOKAN title (English), ボカン GoGoGo logo (logo rule, D5), タツノコプロ end card -> "Tatsunoko Pro".
- BOGO02 story intro (Dokurobey's briefing); BOGO18 an ending. Spoken dialogue, no captions seen at the sampled frames.
  BOGO03-17 sampled but read only at thumbnail size: phase 4 transcribes them and lists any caption.
  Phase 4 read every 2 s sheet (`work/fmv/BOGOxx/`): no caption or sign text in BOGO02-18. The shapes on Dokurobey's
  monitor in BOGO18 (8-10 s, zoomed) are three tiny unicyclists, not kana.
- STAFF.STR (24,152 sectors, ~3 min): scrolling staff roll, Japanese role headings and names, cast list with character
  names, kart pictures, over black. English credits (D3) need this movie re-rendered.

## Duplicates
The same sprite often sits in several archives (machine and course names in MODE, CSELECT, RANK, RESULT, SAVE, DOKURO,
TUP*). The build should replace text by blob hash wherever it occurs, so a missed copy can't stay Japanese.
