# Game state and flow

Addresses are RAM. `SLPS_031.33` loads at 0x80010000 (file offset = addr - 0x8000F800), `$gp` = 0x8003DE84.
Overlays load at 0x80048048 (`OVER/DEMO.BIN` front-end, verified by disassembly; race and movie overlays share it).
**Verified** = read in the disassembly and reached by a `tools/debug/` scene that asserts it from a cold boot.

## Main loop (verified)

`80010FBC` loops forever on **M** = u32 at `8003DEE4` (`$gp+0x60`), dispatching through the 36-entry jump table at
`80010008`. Each handler loads an overlay (`80013128(dest, id)`: 2 movie player, 3 race, 4 front-end), then calls one
function that runs a whole screen and sets the next M before it returns. Poking M mid-screen does nothing until the
screen function returns.

| M | What | Handler |
|---|---|---|
| 0 | init (sound, pads); M+1 | 80011014 |
| 1 | Banpresto logo | DEMO 8004BC04 |
| 2 | opening movie BOGO01 (Start skips) | movie table 80033FC4 #0 |
| 3 | title: PRESS START, then スタート/ロード | DEMO 8004C320 |
| 4, 8 | mode select; story submenu and options run inside it | DEMO 8004EC24 |
| 5, 6 | machine select | DEMO 80057E74 |
| 7 | GP course select (4 courses) | DEMO 80064C44 |
| 9 | movie viewer: movie `$gp+0x58` (byte), back to M=8 | |
| 0xA | story tune-up | DEMO 8005A03C |
| 0xB | ranking (from mode select); after a time attack, ranking + record menu | |
| 0xC | story save screen (after a win) | DEMO 80060924 |
| 0xD, 0xE | time attack record save, ghost save (record menu items 0, 1) | |
| 0x10 | time attack: ghost load (memory card) | |
| 0x11 | game over (GOVER.TMP; §Game over) | DEMO 80064778 |
| 0x17 | race results (GP: レース結果 then 総合結果; time attack; VS) | |
| 0x18 | GP ending: podium (first) or the losers' picture, then M=4 | |
| 0x1A | story post-race (results, Dokurobey); course 7 win goes on to M=0x1F by itself | DEMO 8006F99C |
| 0x1C | VS race (split screen) | |
| 0x1E | time attack race | |
| 0x1F-0x22 | team ending movie, true ending BOGO18, staff roll, post-game save (§After a story race) | |
| 0x23 | DEMO 80073A20 (loads SETU0/SETU1, files 0x108/0x109); no code found that sets it | |
| 0x12 | story intro movie BOGO02, then M=5 | movie table 80033FD4 |
| 0x13 | team movie, table 80033FE4 + 16 x team (`$gp+0x20`); then M=7 if `$gp+0x68` & 2, else M=0xA | |
| 0x14 | movie 80034054 (BOGO10) before course 7, then M=0x19 | |
| 0x15 | warp tunnel after tune-up; M=0x14 if course (`8003DED2`, s16) is 7, else 0x19 | DEMO 800742F8 |
| 0x19 | Dokurobey briefing (DOKURO.TMP) | DEMO 8006F99C |
| 0x1B | story race | race overlay 80049310 |
| 0x1D | GP race | |

`tools/mwrites.py work/demo.dis work/cart.dis [--value N]` lists every M write in a disassembly listing.

Movie table entries (16 bytes: u16 file index, u16 1, u16 1, u16 frames, ..., u16 320, u16 240) start at 80033FC4;
file indexes 0x175-0x186 are BOGO01-BOGO18 in disc order.

## Variables (verified unless marked)

| Address | Size | Meaning |
|---|---|---|
| 8003DEE4 | u32 | M, main state |
| 8003DEA8 | s32 | screen exit flag: a screen loop ends when it reads -1 |
| 8003DED2 | s16 | story course number (guess from 800742F8: 7 plays BOGO10 first) |
| 800BD450 | u32 | front-end frame-buffer index (flips every frame) |
| 800408E6 | u16 | XA music track (5 title, 2 menus, 4 mode select, 8 tune-up); not a screen id |
| 80046A50 | u32[32] | coroutine threads: saved sp; return address at sp+4 (yield 8002D550). Thread 0 runs the screen |
| 801FFA44 | u32 | mode select cursor: 0 story, 1 GP, 2 VS, 3 time attack, 4 ranking, 5 options (thread 0 stack); story submenu uses it too |
| 801FFA5C | u32 | options cursor: 0 controller, 1 machine data, 2 music, 3 movie, 4 back |
| 801FFAC0 | u32 | machine select cursor (7 machines, wraps; GP opens on 4) |
| 801FFBDC | u32 | tune-up cursor: 0 speed, 1 dash, 2 grip, 3 done |

Thread 0 yield sites used as "screen is live" tests: 80052AAC mode select (and its submenus), 8005C068 tune-up.

## Flow from a cold boot (verified by `tools/debug/scenes.lua`)

- Logo (M=1) about frame 420, opening movie (M=2) at 956; Start skips it (pressed early it is ignored, so press
  until M=3). The title animates about 500 frames before PRESS START takes Start; Start again opens スタート/ロード.
- Story: mode select cursor 0, circle, circle (さいしょから) -> M=0x12 movie -> M=5 machine select -> circle ->
  M=0x13 team movie -> M=0xA tune-up -> cursor 3, circle -> M=0x15 warp -> M=0x19 briefing -> M=0x1B race.
- GP: machine select (M=5) -> course select (M=7, pick 4) -> M=0x1D race.
- Time attack: machine select -> ghost load prompt -> M=0x10 memory card load screen.
- VS: machine select waits for player 2.
- Idle at the title returns to the opening movie (no attract race).

## Race (story race, M=0x1B; partly verified)

- Cross accelerates (default button type A). The race does not end until the player finishes: idle for 14,000
  frames the CPUs keep lapping. There is no attract race.
- Kart structs: 7 karts, stride 0x1B4; a u16 track-progress counter at `8003EC84 + i*0x1B4` (rises along the track
  across laps; CPUs reach ~450-540 by frame 14,000). The player is slot 3 (`8003F1A0`) in a story race. The bytes at
  progress-8 and progress-0xC look like laps done (0 player, 1 CPUs at frame 14,000).
- Progress and the -8/-0xC bytes are recomputed from the kart position every frame, so poking them does nothing.
- **Race end (verified, `W.finish_race`):** the story race loop (CART 80049310, overlay base 80048048) runs until
  `8003DD28` (exit flag) is set. The player thread (CART 80049E28, step in s2: 0 countdown, 1 racing, 2 pause menu)
  sets bit 0x400 of the player flags `8003E0E0` when **laps done `8003E1A4` (s32) >= 2**; the finish then sets
  M=0x1A and the exit flag. Writing 2 to `8003E1A4` once the race runs finishes it at once, and the player comes
  first. Placing: u16 rank at `8003ECBC + slot*0x1B4` (0 = first), player slot = u16 `8003E0DC` (3 in story).
  Holding the rank at 3 until the race ends gives a loss.
- **The finish line:** with 0x400 set, the finish also needs `8003E16C` (s32) == 6: the surface type under the player
  kart, rewritten every frame from collision (CART 80051550: kart struct +0x154; 6 = finish-line strip). A parked kart
  is only on it on some courses (0, 3). `W.finish_race` nops that test (bne at CART 8004A0F4, RAM only).
- **Boss races, courses 5 and 7** (thread CART 8004A8E8, not 80049E28): laps do not count. Win when u32 `8003EDF0`
  >= 4 (course 5) / 6 (course 7); lose when u32 `8003EC3C` >= 8 / 12. A loss shows Lose and Dokurobey's
  勝てなかったベェ～ line, then the tune-up (retry).
- **GP and time attack** (thread CART 8004E558): the race ends when player flag 0x20 (`8003E0E0`) is set.
- **VS** (one thread per player, CART 8004D4B8, player structs `8003E018 + 0x348*p`): laps in u32
  `8003E1A0 + 0x348*p`; the race ends once both players have 2.
- Pause menu (step 2): up/down cursor s4, circle: 0 continue, 1 retry (M=0x1B), 2 quit (M=4), 3 title (M=3).

## Other modes (verified by the gp_*, ta_*, vs_*, ranking scenes)

- GP: machine select (M=5) -> M=7 course select: pick 4 courses, このグランプリでよろしいですか (はい) -> M=0x1D race ->
  M=0x17 レース結果, 総合結果 -> next race; after race 4 M=0x18 (podium or losers' picture) -> M=4.
- Time attack: machine select -> ゴーストをロードしますか: はい = M=0x10 card load (ゴーストデータのロード中 /
  ゴーストデータがありません / メモリーカードが差さっていません), いいえ = on -> M=7 one course -> M=0x1E race -> M=0x17
  -> M=0xB ranking; circle opens the record menu (レコードをセーブする M=0xD, ゴーストをセーブする M=0xE, リトライ, コース
  チェンジ, マシンチェンジ, ゲームをやめる). The save screens poll the card and drop most presses.
- VS: needs pad 2 (PCSX-Redux leaves it unplugged: `PCSX.settings.pads[2].Connected`); both players pick -> M=7 ->
  M=0x1C -> M=0x17 (Lose/Win, retry menu) -> M=0x1C.
- Ranking (mode 4): M=0xB, circle back to M=4.
- Machine cursor `801FFAC0` is not the team id `$gp+0x20` (`8003DEA4`): cursor 0 = team 3, cursor 3 = team 5.
- Title ロード of a story save: ファイル1 / マシン / コース, ロードが終了しました, then the story resumes at M=0x12
  (intro movie) -> machine select -> team movie -> tune-up (course 0 for a save made after the course 0 win). The
  story submenu's つづきから did not respond to circle (open).

## After a story race (verified by `race_results`, `stage_clear`, `story_save`, `story_saved`, `story_lose`)

- M=0x1A runs the Dokurobey screen (DEMO 8006F99C, as M=0x19): レース結果 and the placings, then on a win
  Dokurobey's ステージクリア line; the course `8003DED2` goes up by one there. Circle moves on.
- Win: M=0xC save screen (DEMO 80060924; steps in s2, jump table 80049734): メモリーカードをチェック -> slot 1/2 ->
  card check (~600 frames) -> どのファイルに -> ここにセーブしてよろしいですか (はい default) -> セーブ中 ->
  セーブが終了しました. Left/right toggle one yes/no flag shared by the prompts, so circle alone saves to slot 1,
  file 1; circle after the save starts over at the slot prompt, and cross leaves. On exit M=7 if `$gp+0x68` & 2
  (GP), else M=0xA: tune-up for the next course.
- Winning course 7: DEMO 80072304 sets M=0x1F and course 8. M=0x1F plays the team ending (movie table 80034064 +
  16 x team: BOGO14, 17, 12, 11, 13, 16, 15 for teams 0-6), sets u32 `8003E6A8 + 4*team` = 2 (cleared) and goes to
  M=0x20 (BOGO18) if all 7 are cleared, else M=0x21 (STAFF.STR, file 0x187); `$gp+0x2C` = teams cleared (capped
  at 5). M=0x21 -> M=0x22 (save screen, DEMO 80060924) -> M=1 (logo). Game over is M=0x11 (§Game over).
- Team movies (M=0x13, table 80033FE4 + 16 x team): BOGO06, 09, 04, 03, 05, 08, 07.
- Loss: results show the top 3, then an explosion scene, then M=0xA with the course unchanged (retry). Six losses
  in a row still retry: no lives counter.
- Story course select for warps: write the course to `8003DED2` on the tune-up screen; the warp tunnel and race
  load that course (course 7 plays BOGO10 first).

## Memory card

`--sav` gives each run a fresh formatted card (`warp_all.py` writes `work/saves/blank.mcd`). Without it, a story save
lands on the portable `tools/pcsx/memcard1.mcd` and later runs see it. Card result each main-loop frame:
`800CB5B4` (1 done, -1 none/error, 0 busy); the card op step is `800CB5A8`. While the card handler (DEMO 8005C90C)
runs a libcard read, thread 0 is not resumed for several frames (libcard sector waits at 800301A0/800300C8): slow,
not hung.

## Movies that stall (PCSX-Redux headless; open)

BOGO10 after the warp tunnel (M=0x15 -> 0x14) and the team ending after the course 7 race (M=0x1A -> 0x1F) stay
black: MOV_PLAY's StGetNext loop (80048A08, 2000 tries, then a re-seek via 80048C60) never gets a frame. The same
movies play in the movie viewer, and through the same M=0x14 / 0x1F handlers when entered from machine select.
Measured (exec hooks on libcd): the stream's sector callback (8001F638) fires ~23 times and then stops; from the
movie's start the CD command stream (CD_cw 80021030: Setloc, Setmode 0x80, Setmode 0x1E0, ReadS) is identical in
the working and the stalled case. Not the SPU workaround (stalls without it), not dynarec (stalls with the
interpreter), not SPU mute/speed, not the XA real-time bit. Before the stall the warp tunnel leaves 12 SPU voices
keyed (`80040784`) and a second coroutine thread; the working path had XA music streaming. Root cause not found.
Warps: `story_course(7)` enters as course 6 and writes 7 when the briefing starts; `bogo10`, `ending_t*`,
`staff_roll`, `true_ending`, `post_game_save` swap the state at the main loop's dispatch (80010FE4) after machine
select (`W.swap_at_dispatch`); `ending_entry` proves the real flow reaches M=0x1F. Real hardware: untested.

## Game over

M=0x11: EXE 800112C0 calls DEMO 80064778 (music 0x142/0x143), whose task 80064898 loads GOVER.TMP (file 0xF6,
`addiu $a0, $zero, 0xf6` at 80064910) and draws the skull and ゲームオーバー; it exits to M=3 (80064BFC). File index
= line in disc order (0 = SLPS_031.33). No code found that sets M=0x11 (`mwrites.py`, `$gp+0x60` stores) and story
losses (normal and boss) always retry, so it may be unused; the `game_over` warp forces it at dispatch.

## Emulator workaround (warp.lua, RAM only)

The libspu reverb-area clear (80018DB4, WaitEvent at 80018EE4) and SpuIsTransferCompleted (TestEvent loop at
8001E6A4) wait on an SPU DMA event that PCSX-Redux headless never fires when the story race loads (M=0x19). `warp.lua`
nops both waits in RAM every frame. The disc is unchanged; real hardware does not need it.
