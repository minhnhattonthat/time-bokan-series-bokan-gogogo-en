-- Logs the yield site of every coroutine thread whenever it changes: a screen id for menus (docs/re/state.md).
-- Threads: saved sp at 80046A50[i] (yield 8002D550 stores it), return address at sp+4, s0-s7 at sp+8.. Use with --script.
local mem = PCSX.getMemPtr()
local function u32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local N = TASKS or 32
local last = ""
L.on_frame(function(n)
  local t = {}
  for i = 0, N - 1 do
    local sp = u32(0x46A50 + 4 * i)
    if sp >= 0x80000000 and sp < 0x80200000 then
      -- ra, then s2 (sp+0x10): screens keep their step counter there, so a stuck screen shows which step
      t[#t + 1] = string.format("%d:%08X/%X", i, u32(sp + 4), u32(sp + 0x10))
    end
  end
  local s = table.concat(t, " ")
  if s ~= last then L.log(string.format("%d M=%X %s", n, u32(0x3DEE4), s)); last = s end
end)
