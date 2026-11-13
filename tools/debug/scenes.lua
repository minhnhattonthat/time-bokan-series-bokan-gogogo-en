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
  tap_until(function() return W.r32(W.CUR_TUNE) == 3 end, "up", "tune-up cursor on done", 30, 8)
  tap_until(function() return W.m() == 0x15 end, "circle", "M=15 warp", 40)
  if stop == 0x15 then W.frames(280); return end
  W.wait_m(0x19, 1200)
  if stop == 0x19 then W.frames(500); return end
  W.frames(300)
  tap_until(function() return W.m() == 0x1B end, "circle", "M=1B race", 60, 40)
end
W.story = story

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
