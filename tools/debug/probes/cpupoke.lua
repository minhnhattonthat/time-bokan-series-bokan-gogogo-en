-- hold bytes of the player kart (progress field 0x8003F1A0 + off) every frame; log progress
local mem = PCSX.getMemPtr()
L.on_frame(function(n)
  if n >= 30 then for _, p in ipairs(POKES or {}) do mem[0x3F1A0 + p[1]] = p[2] end end
  if n % 300 == 0 then L.log(string.format("%d prog=%d M=%X", n, mem[0x3F1A0] + 256 * mem[0x3F1A1], mem[0x3DEE4])) end
end)
