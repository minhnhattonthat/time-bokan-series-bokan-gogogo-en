-- Scene list for warp.lua: name -> function run as a coroutine from cold boot. See docs/re/state.md.
SCENES = {}
local S = SCENES

-- Thread 0's yield return address: which loop the front-end is waiting in (docs/re/state.md, Threads).
local function ra0() return W.r32(W.r32(0x46A50) + 4) end
W.ra0 = ra0
local function wait_ra(ra, what, limit) W.wait(function() return ra0() == ra end, what, limit or 3000) end
-- Press btn every `gap` frames until cond holds (menus drop presses while they slide in).
local function tap_until(cond, btn, what, gap, limit)
  local n = 0
  while not cond() do
    n = n + 1
    if n > (limit or 60) then error("tap_until timeout: " .. what .. string.format(" M=%X", W.m())) end
    if type(btn) == "function" then btn() else W.tap(btn) end
    W.frames(gap or 20)
  end
  L.log(string.format("%d reached %s", L.frame, what))
end
W.tap_until = tap_until

-- Player 2 pad (VS mode): held 8 frames like W.tap. PCSX-Redux leaves pad 2 unplugged (settings.pads[2].Connected
-- false); W.plug2() plugs it in at run time, only for the scenes that need it.
local pad2 = PCSX.SIO0.slots[2].pads[1]
function W.plug2() PCSX.settings.pads[2].Connected = true end
function W.tap2(btn)
  local b = PCSX.CONSTS.PAD.BUTTON[btn:upper()]
  pad2.setOverride(b); W.frames(8); pad2.clearOverride(b); W.frames(2)
end

-- Cursors are locals on thread 0's stack, so fixed addresses for a given screen (found by ramsearch).
W.CUR_MODE = 0x1FFA44   -- mode select: 0 story, 1 GP, 2 VS, 3 time attack, 4 ranking, 5 options
W.CUR_TUNE = 0x1FFBDC   -- tune-up: 0 speed, 1 dash, 2 grip, 3 done
W.CUR_OPT = 0x1FFA5C    -- options: 0 controller, 1 machine data, 2 music, 3 movie, 4 back
W.CUR_MACHINE = 0x1FFAC0 -- machine select (7 machines, wraps)

local function to_title()
  W.wait_m(2, 3000)
  tap_until(function() return W.m() == 3 end, "start", "M=3 title", 30)
end

local function to_mode_select()
  to_title()
  tap_until(function() return W.m() == 4 end, "start", "M=4 mode select")
  wait_ra(0x80052AAC, "mode select live")
  W.frames(30)
end

-- Moves a cursor kept at `addr` to `want` with down presses (menus wrap).
local function cursor_to(addr, want, what)
  tap_until(function() return W.r32(addr) == want end, "down", what .. " cursor " .. want, 30, 12)
end
W.cursor_to = cursor_to

local function pick_mode(n)
  to_mode_select()
  cursor_to(W.CUR_MODE, n, "mode")
  W.frames(20)
end

S.logo = function()
  W.wait_m(1, 3000)
  W.frames(400)
  W.check(W.m() == 1, "logo state")
  W.done()
end

S.opening = function()
  W.wait_m(2, 3000)
  W.frames(900)
  W.check(W.m() == 2, "opening movie playing")
  W.done()
end

S.title = function()
  to_title()
  W.frames(700)
  W.check(W.m() == 3, "title")
  W.done()
end

S.mode_select = function()
  to_mode_select()
  W.frames(150)
  W.check(W.r32(W.CUR_MODE) == 0, "mode cursor on story")
  W.done()
end

S.title_menu = function()
  to_title()
  wait_ra(0x8004EAC0, "title live")
  W.frames(500)
  tap_until(function() return W.r16(0x408E6) == 2 end, "start", "title menu (music 2)", 60, 10)
  W.frames(120)
  W.check(W.m() == 3, "still title")
  W.done()
end

-- Story mode from さいしょから up to screen M=`stop` (each step taps until the game moves on).
local story_from_tuneup
local function story(stop, machine)
  pick_mode(0)
  tap_until(function() return W.m() == 0x12 end, "circle", "M=12 story intro", 40)
  if stop == 0x12 then W.frames(600); return end
  tap_until(function() return W.m() == 5 end, "start", "M=5 machine select", 30)
  wait_ra(0x80058AAC, "machine select live")
  W.frames(60)
  if machine then
    tap_until(function() return W.r32(W.CUR_MACHINE) == machine end, "right", "machine " .. machine, 30, 12)
  end
  if stop == 5 then return end
  tap_until(function() return W.m() == 0x13 end, "circle", "M=13 team movie", 40)
  if stop == 0x13 then W.frames(600); return end
  tap_until(function() return W.m() == 0xA end, "start", "M=A tune-up", 30)
  wait_ra(0x8005C068, "tune-up live")
  W.frames(60)
  if stop == 0xA then return end
  story_from_tuneup(stop)
end
W.story = story

-- From a live tune-up screen (M=0xA) on to screen `stop`.
story_from_tuneup = function(stop)
  tap_until(function() return W.r32(W.CUR_TUNE) == 3 end, "up", "tune-up cursor on done", 30, 8)
  tap_until(function() return W.m() == 0x15 end, "circle", "M=15 warp", 40)
  if stop == 0x15 then W.frames(280); return end
  W.wait(function() return W.m() == 0x19 end, "M=19", 3000)
  if W.after_warp then W.after_warp() end
  if stop == 0x19 then W.frames(500); return end
  W.frames(300)
  tap_until(function() return W.m() == 0x1B end, "circle", "M=1B race", 60, 40)
end
W.story_from_tuneup = story_from_tuneup

S.story_menu = function()
  pick_mode(0)
  tap_until(function() return W.r32(W.CUR_MODE) == 0 and W.r16(0x408E6) == 2 end, "circle", "story submenu", 40, 3)
  W.frames(200)
  W.check(W.m() == 4, "still mode select")
  W.done()
end
S.story_intro = function() story(0x12); W.check(W.m() == 0x12, "intro movie"); W.done() end
S.story_machine = function() story(5); W.check(W.m() == 5, "machine select"); W.done() end
S.team_movie = function() story(0x13); W.check(W.m() == 0x13, "team movie"); W.done() end
S.tuneup = function() story(0xA); W.check(W.m() == 0xA, "tune-up"); W.done() end
S.warp = function() story(0x15); W.check(W.m() == 0x15, "warp tunnel"); W.done() end
S.briefing = function() story(0x19); W.check(W.m() == 0x19, "briefing"); W.done() end
S.race_story = function() story(0x1B); W.frames(900); W.check(W.m() == 0x1B, "story race"); W.done() end

-- Race end (docs/re/state.md §Race): the player thread finishes the player when laps done (8003E1A4) reaches 2; the
-- placing is the kart's rank (u16 at 8003ECBC + slot*0x1B4, 0 = first), slot = u16 8003E0DC. Lap poke alone puts
-- the player first. A rank > 0 is held every frame until the race ends (the other karts' ranks are left as they are).
W.LAPS = 0x3E1A4
W.COURSE = 0x3DED2
local function rank_addr() return 0x3ECBC + W.r16(0x3E0DC) * 0x1B4 end
local function finish_race(rank, race_m)
  race_m = race_m or 0x1B
  W.wait_m(race_m, 600)
  -- held every frame: the race start resets it, and the check only runs once the countdown is over
  -- Courses 5 and 7 are boss races (thread CART 8004A8E8): won when u32 8003EDF0 reaches 4 / 6, lost when u32
  -- 8003EC3C reaches 8 / 12. Laps do not count there.
  local boss = ({ [5] = { 4, 8 }, [7] = { 6, 12 } })[W.r16(W.COURSE)]
  local n = 0
  while W.m() == race_m do
    if boss then
      if rank and rank > 0 then W.w32(0x3EC3C, boss[2]) else W.w32(0x3EDF0, boss[1]) end
    end
    W.w8(W.LAPS, 2)
    -- GP/time-attack races (thread CART 8004E558) finish when player flag 0x20 (8003E0E0) is set.
    if race_m ~= 0x1B then W.w32(0x3E0E0, bit.bor(W.r32(0x3E0E0), 0x20)) end
    -- VS races (one thread per player, CART 8004D4B8; player structs 8003E018 + 0x348*p) count laps in u32
    -- 8003E1A0 + 0x348*p.
    if race_m == 0x1C then W.w32(0x3E1A0, 2); W.w32(0x3E1A0 + 0x348, 2) end
    -- The finish also needs the kart on the finish-line surface (8003E16C = 6, set from collision each frame), which
    -- a parked kart only is on some courses: skip that test (bne at CART 8004A0F4, RAM only; the overlay reloads).
    if W.r32(0x4A0F4) == 0x14620049 then W.w32(0x4A0F4, 0) end
    -- story: the lap poke alone puts the player first; GP/VS/time attack need rank 0 held too
    if rank and (rank > 0 or race_m ~= 0x1B) then W.w16(rank_addr(), rank) end
    n = n + 1
    if n > 6000 then error("race did not end") end
    coroutine.yield()
  end
  L.log(string.format("%d race over, rank %d, M=%X", L.frame, W.r16(rank_addr()), W.m()))
end
W.finish_race = finish_race

-- Story from a cold boot to course `course` (0-7), stopping at screen `stop` (default the race).
-- Course 7 would play BOGO10 (M=0x14) after the tunnel, and that stream stalls in PCSX-Redux headless (StGetNext
-- never gets a sector, MOV_PLAY 80048A08), so it enters as course 6 and becomes 7 on the briefing's first frame.
local function story_course(course, stop)
  story(0xA)
  W.w16(W.COURSE, course == 7 and 6 or course)
  if course == 7 then W.after_warp = function() W.w16(W.COURSE, 7) end end
  story_from_tuneup(stop or 0x1B)
  W.after_warp = nil
end

-- Story save screen (M=0xC, after a won race): circle picks slot 1, file 1, はい (left/right toggle one flag shared
-- by every prompt, so circle alone is right). The card check takes ~600 frames; presses during it are dropped.
-- After セーブが終了しました circle starts over at the slot prompt; cross leaves (M=0xA, or M=7 in GP).
-- Save screens poll the card and drop most presses, so circle goes in every 50 frames (~1900 frames: the save is
-- done by then), with a shot after each (s01-s32): every message of the flow lands in one of them.
function W.save_presses(n)
  for i = 1, n or 32 do W.tap("circle"); W.frames(50); W.shot(string.format("s%02d", i)) end
end
local function save_through()
  W.save_presses()
  tap_until(function() return W.m() ~= 0xC end, "cross", "left save screen", 60, 40)
end

S.race_results = function()
  story(0x1B); finish_race(0)
  W.check(W.m() == 0x1A, "post-race (M=1A)")
  W.frames(800) -- レース結果 title, then the placings
  W.done()
end
S.stage_clear = function()
  story(0x1B); finish_race(0)
  W.frames(800)
  for _ = 1, 3 do W.tap("circle"); W.frames(60) end
  W.frames(240) -- Dokurobey's ステージクリア line (the course goes up when it closes)
  W.check(W.m() == 0x1A, "still post-race")
  W.done()
end
S.story_save = function()
  story(0x1B); finish_race(0)
  tap_until(function() return W.m() == 0xC end, "circle", "M=C save", 60, 40)
  W.frames(300)
  W.done()
end
S.story_saved = function()
  story(0x1B); finish_race(0)
  tap_until(function() return W.m() == 0xC end, "circle", "M=C save", 60, 40)
  save_through()
  W.wait_m(0xA, 600)
  wait_ra(0x8005C068, "tune-up live")
  W.frames(120)
  W.check(W.r16(W.COURSE) == 1, "tune-up for course 1")
  W.done()
end
S.story_lose = function()
  story(0x1B); finish_race(3)
  W.check(W.m() == 0x1A, "post-race (M=1A)")
  W.frames(420)
  tap_until(function() return W.m() ~= 0x1A end, "circle", "lose scene", 60, 30)
  wait_ra(0x8005C068, "tune-up live")
  W.frames(120)
  W.check(W.m() == 0xA and W.r16(W.COURSE) == 0, "retry at tune-up, course 0")
  W.done()
end

-- Endings: winning course 7 sets M=0x1F (team ending, BOGO11-17 by team `$gp+0x20`), which marks the team cleared
-- (u32 8003E6A8 + 4*team = 2) and goes to M=0x20 (BOGO18) once all 7 are, else to M=0x21 (staff roll, STAFF.STR),
-- then M=0x22 (save screen) and M=1.
-- ending_entry proves the real flow (win course 7 -> M=0x1F). Its movie then stalls in PCSX-Redux headless, as BOGO10
-- does after the warp tunnel (docs/re/state.md §Movies that stall), so the movie scenes enter the same handler from
-- machine select instead: M=0x13 (team movie, just set) is replaced by the wanted state before the handler runs.
S.ending_entry = function()
  story_course(7)
  finish_race(0)
  for i = 1, 6 do W.frames(120); W.shot("results" .. i) end -- the course 7 win goes to M=0x1F by itself
  tap_until(function() return W.m() == 0x1F end, "circle", "M=1F ending", 60, 40)
  W.frames(60)
  W.check(W.m() == 0x1F, "team ending state after the course 7 win")
  W.done()
end
-- Machine select (machine = team 0-6) -> state `m` in place of the team movie. The swap happens at the main loop's
-- dispatch (80010FE4, an exec hook: warp_all.py runs these scenes with --debugger); a write one frame later is too
-- late, the 0x12-0x14 movie handler has already been entered.
-- `team` ($gp+0x20, 8003DEA4) is written there too: the machine cursor is not the team id (cursor 0 = team 3,
-- cursor 3 = team 5).
W.TEAM = 0x3DEA4
-- The next time the main loop dispatches state `from`, it runs `to` instead (once).
function W.swap_at_dispatch(from, to, team)
  local pending = true
  L.on_exec(0x80010FE4, function()
    if pending and W.m() == from then
      W.w32(W.M, to)
      if team then W.w32(W.TEAM, team) end
      pending = false
    end
  end)
end
local function from_machine_select(m, team)
  W.swap_at_dispatch(0x13, m, team)
  story(5)
  tap_until(function() return W.m() == m end, "circle", string.format("M=13 -> M=%X", m), 40)
end
W.from_machine_select = from_machine_select
-- names: ending_t0 ending_t1 ending_t2 ending_t3 ending_t4 ending_t5 ending_t6
for t = 0, 6 do
  S["ending_t" .. t] = function()
    from_machine_select(0x1F, t)
    W.frames(900)
    W.check(W.m() == 0x1F and W.r32(W.TEAM) == t,
      string.format("team %d ending movie (M=%X team=%d)", t, W.m(), W.r32(W.TEAM)))
    W.done()
  end
end
-- Each team's story movie (M=0x13: BOGO06, 09, 04, 03, 05, 08, 07 for teams 0-6).
-- names: team_movie_t0 team_movie_t1 team_movie_t2 team_movie_t3 team_movie_t4 team_movie_t5 team_movie_t6
for t = 0, 6 do
  S["team_movie_t" .. t] = function()
    from_machine_select(0x13, t)
    W.frames(600)
    W.check(W.m() == 0x13 and W.r32(W.TEAM) == t, "team " .. t .. " movie")
    W.done()
  end
end
S.bogo10 = function() -- the movie before course 7 (M=0x14), then the briefing
  story(5)
  W.w16(W.COURSE, 7)
  tap_until(function() return W.m() == 0x13 end, "circle", "M=13", 40)
  W.w32(W.M, 0x14)
  W.frames(700)
  W.check(W.m() == 0x14, "BOGO10 playing")
  W.done()
end
S.staff_roll = function()
  from_machine_select(0x1F)
  W.wait_m(0x21, 12000)
  W.frames(1500)
  W.check(W.m() == 0x21, "staff roll movie")
  W.done()
end
-- Game over (M=0x11, EXE 800112C0 -> DEMO 80064778, GOVER.TMP). No code found that sets M=0x11: forced at dispatch.
S.game_over = function()
  from_machine_select(0x11)
  W.frames(600)
  W.check(W.m() == 0x11, "game over screen")
  W.done()
end
S.true_ending = function()
  for t = 0, 6 do W.w32(0x3E6A8 + 4 * t, 2) end
  from_machine_select(0x1F)
  for t = 0, 6 do W.w32(0x3E6A8 + 4 * t, 2) end -- new game may clear them
  W.wait_m(0x20, 12000)
  W.frames(900)
  W.check(W.m() == 0x20, "true ending movie BOGO18")
  W.done()
end
S.post_game_save = function()
  from_machine_select(0x1F)
  W.wait_m(0x22, 25000)
  W.frames(600)
  W.check(W.m() == 0x22, "post-game save screen")
  W.done()
end

-- Shots p01..pNN every `every` frames, circle after every `tap`-th one: pages of text that circle advances.
function W.shoot_through(n, every, tap)
  local last = -1
  for i = 1, n do
    W.frames(every); W.shot(string.format("p%02d", i))
    if W.m() ~= last then L.log(string.format("%d M=%X", L.frame, W.m())); last = W.m() end
    if i % tap == 0 then W.tap("circle") end
  end
end

-- Per story course: the Dokurobey briefing pages, and the post-race screens after a win (results, his stage-clear
-- line, the save screen; course 7 goes on to the ending) and after a loss (courses 5 and 7 are boss races).
-- names: briefing_c0 briefing_c1 briefing_c2 briefing_c3 briefing_c4 briefing_c5 briefing_c6 briefing_c7
-- names: win_c0 win_c1 win_c2 win_c3 win_c4 win_c5 win_c6 win_c7 boss_lose_c5 boss_lose_c7
for c = 0, 7 do
  S["briefing_c" .. c] = function()
    story_course(c, 0x19)
    W.shoot_through(16, 100, 2)
    W.check(W.r16(W.COURSE) == c, "briefing for course " .. c)
    W.done()
  end
  S["win_c" .. c] = function()
    story_course(c)
    finish_race(0)
    W.shoot_through(20, 100, 3)
    W.done()
  end
end
for _, c in ipairs({ 5, 7 }) do
  S["boss_lose_c" .. c] = function()
    story_course(c)
    finish_race(3)
    W.shoot_through(20, 100, 3)
    W.check(W.m() == 0xA, "retry at the tune-up")
    W.done()
  end
end

-- One race per story course: race_c0 .. race_c7 (course 7 plays BOGO10 before the briefing).
-- names: race_c0 race_c1 race_c2 race_c3 race_c4 race_c5 race_c6 race_c7
for c = 0, 7 do
  S["race_c" .. c] = function()
    story_course(c)
    W.frames(900)
    W.check(W.m() == 0x1B and W.r16(W.COURSE) == c, "story race course " .. c)
    W.done()
  end
end

-- Options (mode select cursor 5): cursor 801FFA5C 0 controller, 1 machine data, 2 music, 3 movie list, 4 back.
local function options(item)
  pick_mode(5)
  W.tap("circle"); W.frames(150)
  if item == nil then return end
  cursor_to(W.CUR_OPT, item, "options")
  W.frames(30)
  W.tap("circle"); W.frames(400)
end
S.options = function() options(); W.check(W.m() == 4, "options (in mode select)"); W.done() end
S.opt_controller = function() options(0); W.check(W.m() == 4, "controller setup"); W.done() end
S.opt_machine_data = function() options(1); W.check(W.m() == 4, "machine data"); W.done() end
S.opt_music = function() options(2); W.check(W.m() == 4, "music test"); W.done() end
S.opt_movies = function() options(3); W.check(W.m() == 4, "movie list"); W.done() end
-- Machine data: one page per machine (down); movie list: 6 tabs (right).
-- names: machine_data_1 machine_data_2 machine_data_3 machine_data_4 machine_data_5 machine_data_6
-- names: movie_tab_1 movie_tab_2 movie_tab_3 movie_tab_4 movie_tab_5
for i = 1, 6 do
  S["machine_data_" .. i] = function()
    options(1)
    for _ = 1, i do W.tap("down"); W.frames(40) end
    W.frames(200)
    W.check(W.m() == 4, "machine data page " .. i)
    W.done()
  end
  if i <= 5 then
    S["movie_tab_" .. i] = function()
      options(3)
      for _ = 1, i do W.tap("right"); W.frames(40) end
      W.frames(200)
      W.check(W.m() == 4, "movie list tab " .. i)
      W.done()
    end
  end
end

-- Movie viewer: circle on the movie list sets M=9, which plays movie table entry `$gp+0x58` (8003DEDC, byte; table
-- 80033FC4: 0 BOGO01, 1 BOGO02, 2-8 team movies, 9 BOGO10, 10-16 team endings, 17 BOGO18, 18 STAFF). The handler
-- loads its overlay before it reads the index, so writing it on the first frame of M=9 picks the movie.
-- names: movie_00 movie_01 movie_02 movie_03 movie_04 movie_05 movie_06 movie_07 movie_08 movie_09 movie_10 movie_11 movie_12 movie_13 movie_14 movie_15 movie_16 movie_17 movie_18
for i = 0, 18 do
  S[string.format("movie_%02d", i)] = function()
    options(3)
    tap_until(function() return W.m() == 9 end, "circle", "M=9 movie viewer", 40, 10)
    W.w8(0x3DEDC, i)
    W.frames(900)
    W.check(W.m() == 9 and W.r8(0x3DEDC) == i, "viewer playing movie " .. i)
    W.done()
  end
end

-- GP (mode 1): machine select (M=5) -> course select (M=7: pick 4 courses, then このグランプリでよろしいですか, はい)
-- -> race M=0x1D -> M=0x17 レース結果, 総合結果 -> next race ... after race 4: M=0x18 GP ending (podium when
-- first, else the losers' picture) -> mode select (M=4). Time attack (mode 3): machine select -> ゴーストをロード
-- しますか (はい: M=0x10 card load; いいえ: on) -> M=7 one course -> race M=0x1E -> M=0x17 -> M=0xB ranking with
-- the record menu (レコードをセーブする, ゴーストをセーブする, リトライ, コースチェンジ, マシンチェンジ, ゲームをやめる)
-- -> M=0xD save screen. VS (mode 2, pad 2 plugged in): both pick -> M=7 course -> race M=0x1C -> M=0x17 -> M=0x1C.
local function gp_courses()
  pick_mode(1)
  tap_until(function() return W.m() == 7 end, "circle", "M=7 course select", 60, 20)
  W.frames(300)
end
local function gp_race(n) -- from the course select (4 picked) to race n (1-4)
  for i = 1, n do
    tap_until(function() return W.m() == 0x1D end, "circle", "GP race " .. i, 60, 40)
    if i < n then
      W.frames(300); finish_race(0, 0x1D)
      tap_until(function() return W.m() ~= 0x17 end, "circle", "after results " .. i, 60, 40)
    end
  end
end
S.gp_machine = function()
  pick_mode(1)
  tap_until(function() return W.m() == 5 end, "circle", "M=5", 60, 20)
  wait_ra(0x80058AAC, "machine select live")
  W.frames(120)
  W.check(W.m() == 5, "GP machine select")
  W.done()
end
S.gp_courses = function()
  gp_courses()
  for _ = 1, 2 do W.tap("circle"); W.frames(120) end
  W.check(W.m() == 7, "GP course select, 2 picked")
  W.done()
end
S.gp_confirm = function()
  gp_courses()
  for _ = 1, 4 do W.tap("circle"); W.frames(120) end
  W.check(W.m() == 7, "GP confirm prompt")
  W.done()
end
S.gp_race = function() gp_courses(); gp_race(1); W.frames(900); W.check(W.m() == 0x1D, "GP race 1"); W.done() end
S.gp_race4 = function() gp_courses(); gp_race(4); W.frames(900); W.check(W.m() == 0x1D, "GP race 4"); W.done() end
S.gp_results = function()
  gp_courses(); gp_race(1); W.frames(300); finish_race(0, 0x1D)
  W.frames(240); W.tap("circle"); W.frames(150); W.tap("circle"); W.frames(150)
  W.check(W.m() == 0x17, "GP race results")
  W.done()
end
S.gp_total = function()
  gp_courses(); gp_race(1); W.frames(300); finish_race(0, 0x1D)
  for _ = 1, 4 do W.frames(150); W.tap("circle") end
  W.frames(150)
  W.check(W.m() == 0x17, "GP total results")
  W.done()
end
local function gp_end(rank)
  gp_courses(); gp_race(4); W.frames(300); finish_race(rank, 0x1D)
  tap_until(function() return W.m() == 0x18 end, "circle", "M=18 GP ending", 60, 40)
  for i = 1, 8 do W.frames(50); W.shot("end" .. i) end -- the picture fades in ~350 frames after M=0x18
  W.wait_m(0x18, 1)
  W.check(W.m() == 0x18, "GP ending")
  W.done()
end
S.gp_win = function() gp_end(0) end
S.gp_lose = function() gp_end(6) end

local function ta_ghost_prompt()
  pick_mode(3)
  tap_until(function() return W.m() == 5 end, "circle", "M=5", 60, 20)
  wait_ra(0x80058AAC, "machine select live")
  W.frames(120)
  W.tap("circle"); W.frames(200) -- ゴーストをロードしますか
end
local function ta_race()
  ta_ghost_prompt()
  W.tap("right"); W.frames(60) -- いいえ
  tap_until(function() return W.m() == 7 end, "circle", "M=7 TA course select", 60, 20)
  W.frames(300)
  tap_until(function() return W.m() == 0x1E end, "circle", "M=1E TA race", 60, 40)
end
local function ta_menu()
  ta_race(); W.frames(300); finish_race(0, 0x1E)
  tap_until(function() return W.m() == 0xB end, "circle", "M=B record menu", 60, 40)
  W.frames(300)
  W.tap("circle"); W.frames(90) -- the menu opens over the ranking
end
S.ta_ghost_prompt = function() ta_ghost_prompt(); W.check(W.m() == 5, "ghost load prompt"); W.done() end
S.ta_ghost_load = function() -- はい with no ghost on the card: ゴーストデータがありません
  ta_ghost_prompt()
  tap_until(function() return W.m() == 0x10 end, "circle", "M=10 ghost load", 60, 20)
  for _ = 1, 3 do W.frames(200); W.tap("circle") end
  W.frames(300)
  W.check(W.m() == 0x10, "ghost load screen")
  W.done()
end
S.ta_courses = function()
  ta_ghost_prompt(); W.tap("right"); W.frames(60)
  tap_until(function() return W.m() == 7 end, "circle", "M=7 TA course select", 60, 20)
  W.frames(300)
  W.done()
end
S.ta_race = function() ta_race(); W.frames(900); W.check(W.m() == 0x1E, "time attack race"); W.done() end
S.ta_results = function()
  ta_race(); W.frames(300); finish_race(0, 0x1E)
  W.frames(480)
  W.check(W.m() == 0x17, "time attack results")
  W.done()
end
S.ta_menu = function() ta_menu(); W.check(W.m() == 0xB, "record menu"); W.done() end
local function ta_save(item) -- record menu item 0 record save (M=0xD), 1 ghost save (M=0xE)
  ta_menu()
  for _ = 1, item do W.tap("down"); W.frames(40) end
  local m = 0xD + item
  tap_until(function() return W.m() == m end, "circle", string.format("M=%X save", m), 60, 20)
end
S.ta_save = function() ta_save(0); W.frames(300); W.check(W.m() == 0xD, "record save screen"); W.done() end
-- Save screen (M=0xD): slot prompt -> card check (~700 frames, presses dropped) -> このデータをセーブしますか (はい)
-- -> ベストタイムのセーブ中.
local function ta_save_through(item, done_what)
  ta_save(item)
  W.save_presses()
  W.check(W.m() == 0xD + item, done_what)
  W.done()
end
S.ta_saved = function() ta_save_through(0, "record saving") end
S.ta_ghost_save = function() ta_save_through(1, "ghost saving") end

S.ranking = function()
  pick_mode(4)
  tap_until(function() return W.m() == 0xB end, "circle", "M=B ranking", 60, 20)
  W.frames(300)
  W.check(W.m() == 0xB, "ranking")
  W.done()
end

local function vs_machine()
  W.plug2()
  pick_mode(2)
  tap_until(function() return W.m() == 5 end, "circle", "M=5", 60, 20)
  wait_ra(0x80058AAC, "machine select live")
  W.frames(120)
end
local function vs_race()
  vs_machine()
  tap_until(function() return W.m() == 7 end, function() W.tap("circle"); W.tap2("circle") end, "M=7", 60, 20)
  W.frames(300)
  tap_until(function() return W.m() == 0x1C end, function() W.tap("circle"); W.tap2("circle") end, "M=1C", 60, 20)
end
S.vs_machine = function() vs_machine(); W.tap2("right"); W.frames(60); W.check(W.m() == 5, "VS machine select"); W.done() end
S.vs_courses = function()
  vs_machine()
  tap_until(function() return W.m() == 7 end, function() W.tap("circle"); W.tap2("circle") end, "M=7", 60, 20)
  W.frames(300)
  W.done()
end
S.vs_race = function() vs_race(); W.frames(900); W.check(W.m() == 0x1C, "VS race"); W.done() end
S.vs_results = function()
  vs_race(); W.frames(300); finish_race(0, 0x1C)
  W.frames(300)
  W.check(W.m() == 0x17, "VS results")
  W.done()
end

-- Memory card scenes. warp_all.py boots these with the card another scene wrote (CARD_FROM there); the nocard_*
-- scenes pull both cards out (PCSX-Redux settings, at run time).
function W.unplug_cards()
  PCSX.settings.emulator.Mcd1Inserted = false
  PCSX.settings.emulator.Mcd2Inserted = false
end
local function title_menu_open()
  to_title()
  wait_ra(0x8004EAC0, "title live")
  W.frames(500)
  tap_until(function() return W.r16(0x408E6) == 2 end, "start", "title menu (music 2)", 60, 10)
  W.frames(120)
end
local function title_load(n)
  title_menu_open()
  W.tap("down"); W.frames(40)
  W.save_presses(n)
end
-- card from story_saved; 18 presses end on the save file list (runs are deterministic)
S.title_load = function() title_load(18); W.frames(30); W.check(W.m() <= 4, "title load screen M=" .. W.m()); W.done() end
-- Title ロード of a story save resumes the story: M=0x12 intro movie -> machine select -> team movie -> tune-up
-- (card from story_saved).
S.story_resume = function()
  title_load()
  tap_until(function() return W.m() == 5 end, "start", "M=5 machine select", 60, 30)
  wait_ra(0x80058AAC, "machine select live")
  W.frames(60)
  tap_until(function() return W.m() == 0x13 end, "circle", "M=13 team movie", 40)
  tap_until(function() return W.m() == 0xA end, "start", "M=A tune-up", 30)
  wait_ra(0x8005C068, "tune-up live")
  W.frames(120)
  -- the save after the course 0 win lists コース ジュラッキパーク and resumes at course 0
  W.check(W.m() == 0xA, "resumed story at the tune-up, course=" .. W.r16(W.COURSE))
  W.done()
end
S.ta_ghost_loaded = function() -- はい, card from ta_ghost_save
  ta_ghost_prompt()
  tap_until(function() return W.m() == 0x10 end, "circle", "M=10 ghost load", 60, 20)
  W.save_presses()
  W.done()
end
S.nocard_title_load = function() W.unplug_cards(); title_load(); W.done() end
S.nocard_story_save = function()
  W.unplug_cards()
  story(0x1B); finish_race(0)
  tap_until(function() return W.m() == 0xC end, "circle", "M=C save", 60, 40)
  W.save_presses()
  W.done()
end
S.nocard_ta_ghost = function()
  W.unplug_cards()
  ta_ghost_prompt()
  tap_until(function() return W.m() == 0x10 end, "circle", "M=10 ghost load", 60, 20)
  W.save_presses()
  W.done()
end

-- Pause menu (story race, start): continue, retry, quit, title.
S.pause = function()
  story(0x1B); W.frames(1300) -- past the countdown
  W.tap("start"); W.frames(90)
  W.check(W.m() == 0x1B, "paused race")
  W.done()
end
