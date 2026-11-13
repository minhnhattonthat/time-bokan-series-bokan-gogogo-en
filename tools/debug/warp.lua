-- Cold-boot warp: plays each scene in tools/debug/scenes.lua as a coroutine that waits on game state, never on frame
-- counts it hopes are right. Addresses and state numbers: docs/re/state.md.
-- Use: emu.py CUE --out D --frames 40000 --timeout 900 --script tools/debug/warp.lua --script tools/debug/scenes.lua
--      --var "SCENE='title'". warp_all.py runs the whole list.
local mem = PCSX.getMemPtr()
W = {}
function W.r8(a) return mem[a % 0x200000] end
function W.r16(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 end
function W.r32(a) return W.r16(a) + W.r16(a + 2) * 65536 end
function W.w8(a, v) mem[a % 0x200000] = v % 256 end
function W.w16(a, v) a = a % 0x200000; mem[a] = v % 256; mem[a + 1] = math.floor(v / 256) % 256 end
function W.w32(a, v) W.w16(a, v % 65536); W.w16(a + 2, math.floor(v / 65536) % 65536) end

-- Game state variables (docs/re/state.md). gp = 0x8003DE84.
W.M = 0x3DEE4      -- main state ($gp+0x60), jump table 80010008 in 80010FBC

local checks = {}
function W.frames(n) for _ = 1, n do coroutine.yield() end end
function W.m() return W.r32(W.M) end
-- Fails the run (exit 2) if the game never reaches the state: a wrong warp must not pass as a shot of something else.
function W.wait(cond, what, limit)
  limit = limit or 6000
  local n = 0
  while not cond() do
    n = n + 1
    if n > limit then error("warp timeout waiting for " .. tostring(what) .. string.format(" M=%X", W.m())) end
    coroutine.yield()
  end
  L.log(string.format("%d reached %s", L.frame, tostring(what)))
end
function W.wait_m(m, limit) W.wait(function() return W.m() == m end, string.format("M=%X", m), limit) end
function W.tap(btn, hold) L.press(btn, hold or 8); L.press("-", 2); W.frames((hold or 8) + 2) end
function W.shot(name) L.shot(name .. ".png"); L.log(string.format("%d shot %s", L.frame, name)) end
function W.check(ok, what)
  checks[#checks + 1] = what
  if not ok then error("check failed: " .. what) end
  L.log("check ok: " .. what)
end
function W.done()
  L.shot("final.png")
  L.log(string.format("warp done %s frame %d", SCENE, L.frame))
  if STATE_OUT then L.save_state(STATE_OUT) end
  L.finish(0)
  while true do coroutine.yield() end
end

-- Emulator workaround (RAM only, never the disc): the SPU reverb-area clear 80018DB4 waits on an SPU DMA event
-- (WaitEvent at 80018EE4) that PCSX-Redux headless never fires when a story race loads (M=0x19), and
-- SpuIsTransferCompleted's wait loop (TestEvent, 8001E6A4-8001E6B4) spins on the same event. Skip both waits.
function W.qa_patches()
  if W.r32(0x18EE4) == 0x0C00B2CD then W.w32(0x18EE4, 0) end
  if W.r32(0x1E6B4) == 0x1040FFFB then W.w32(0x1E6B4, 0) end
end

local co
L.on_frame(function()
  W.qa_patches()
  if not co then
    if not SCENES then error("load tools/debug/scenes.lua with --script") end
    local fn = SCENES[SCENE]
    if not fn then error("unknown scene " .. tostring(SCENE)) end
    co = coroutine.create(fn)
  end
  if GOD and W.god then W.god() end
  local ok, e = coroutine.resume(co)
  if not ok then error(e) end
end)
