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
| 0xB | ranking | |
| 0x10 | time attack: ghost load (memory card) | |
| 0x12 | story intro movie BOGO02, then M=5 | movie table 80033FD4 |
| 0x13 | team movie, table 80033FE4 + 16 x team (`$gp+0x20`); then M=7 if `$gp+0x68` & 2, else M=0xA | |
| 0x14 | movie 80034054 (BOGO10) before course 7, then M=0x19 | |
| 0x15 | warp tunnel after tune-up; M=0x14 if course (`8003DED2`, s16) is 7, else 0x19 | DEMO 800742F8 |
| 0x19 | Dokurobey briefing (DOKURO.TMP) | DEMO 8006F99C |
| 0x1B | story race | race overlay 80049310 |
| 0x1D | GP race | |

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
- Pause menu (step 2): up/down cursor s4, circle: 0 continue, 1 retry (M=0x1B), 2 quit (M=4), 3 title (M=3).

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
  at 5). M=0x21 -> M=0x22 (save screen, DEMO 80060924) -> M=1 (logo). M=0x23 runs DEMO 80073A20 (not reached yet).
- Team movies (M=0x13, table 80033FE4 + 16 x team): BOGO06, 09, 04, 03, 05, 08, 07.
- Loss: results show the top 3, then an explosion scene, then M=0xA with the course unchanged (retry). Game over
  (GOVER) not reached yet: no lives counter seen after one loss.
- Story course select for warps: write the course to `8003DED2` on the tune-up screen; the warp tunnel and race
  load that course (course 7 plays BOGO10 first).

## Memory card

`--sav` gives each run a fresh formatted card (`warp_all.py` writes `work/saves/blank.mcd`). Without it, a story save
lands on the portable `tools/pcsx/memcard1.mcd` and later runs see it. Card result each main-loop frame:
`800CB5B4` (1 done, -1 none/error, 0 busy); the card op step is `800CB5A8`. While the card handler (DEMO 8005C90C)
runs a libcard read, thread 0 is not resumed for several frames (libcard sector waits at 800301A0/800300C8): slow,
not hung.

## BOGO10 stalls headless (open)

Course 7's warp tunnel goes to M=0x14, which plays BOGO10; in PCSX-Redux headless the stream never delivers a
sector (MOV_PLAY 80048A08 retries StGetNext 2000 times, over and over) and the screen stays black. BOGO01, 02 and the
team movies play. `story_course(7)` sidesteps it (enters as course 6, writes 7 when the briefing starts). Check BOGO10
in the movie viewer (M=9) before blaming the emulator.

## Emulator workaround (warp.lua, RAM only)

The libspu reverb-area clear (80018DB4, WaitEvent at 80018EE4) and SpuIsTransferCompleted (TestEvent loop at
8001E6A4) wait on an SPU DMA event that PCSX-Redux headless never fires when the story race loads (M=0x19). `warp.lua`
nops both waits in RAM every frame. The disc is unchanged; real hardware does not need it.
