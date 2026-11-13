local mem = PCSX.getMemPtr()
local function u32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
L.on_frame(function(n)
  if n % 60 == 0 and n > (PC_FROM or 0) then
    local r = PCSX.getRegisters()
    L.log(string.format("%d pc=%08X ra=%08X M=%X exit=%X", n, r.pc, r.GPR.n.ra, u32(0x3DEE4), u32(0x3DEA8)))
  end
end)
