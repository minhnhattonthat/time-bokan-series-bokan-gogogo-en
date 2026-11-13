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
    W.tap(btn); W.frames(gap or 20)
  end
  L.log(string.format("%d reached %s", L.frame, what))
end
W.tap_until = tap_until

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
local function finish_race(rank)
  W.wait_m(0x1B, 600)
  -- held every frame: the race start resets it, and the check only runs once the countdown is over
  local n = 0
  while W.m() == 0x1B do
    W.w8(W.LAPS, 2)
    if rank and rank > 0 then W.w16(rank_addr(), rank) end
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
local function save_through()
  for _ = 1, 32 do W.tap("circle"); W.frames(50) end -- ~1900 frames: the save is done by then
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
local function win_story(all_teams)
  story_course(7)
  if all_teams then for t = 0, 6 do W.w32(0x3E6A8 + 4 * t, 2) end end
  finish_race(0)
  tap_until(function() return W.m() == 0x1F end, "circle", "M=1F ending", 60, 40)
end
S.ending = function()
  win_story()
  W.frames(900)
  W.check(W.m() == 0x1F, "team ending movie")
  W.done()
end
S.true_ending = function()
  win_story(true)
  W.wait_m(0x20, 9000)
  W.frames(600)
  W.done()
end
S.staff_roll = function()
  win_story()
  W.wait_m(0x21, 9000)
  W.frames(1500)
  W.check(W.m() == 0x21, "staff roll movie")
  W.done()
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
