-- Logs every change of the game's state variables (addresses: docs/re/state.md). Use with --script.
-- Extra addresses: --var "WATCH={0x408E6, 0x400A0}" (u16 each, physical or 0x80-based).
local mem = PCSX.getMemPtr()
local function u16(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 end
local VARS = {}
for _, a in ipairs(WATCH or {}) do VARS[#VARS + 1] = { string.format("%X", a % 0x200000), a } end
if STATE_VARS then for _, v in ipairs(STATE_VARS) do VARS[#VARS + 1] = v end end
local last = {}
L.on_frame(function(n)
  local s, ch = {}, false
  for _, v in ipairs(VARS) do
    local x = u16(v[2])
    s[#s + 1] = string.format("%s=%X", v[1], x)
    if last[v[1]] ~= x then ch = true end
    last[v[1]] = x
  end
  if ch then L.log(n .. " " .. table.concat(s, " ")) end
end)
