-- With warp.lua and scenes.lua: dump GPU VRAM beside every warp shot (<name>.vram.bin, 1 MB) for tools/gfx_cover.py.
-- Use: warp_all.py --rom CUE --out DIR --script tools/debug/vramshot.lua
local shot, done = W.shot, W.done
function W.shot(name) shot(name); L.dump_ppu(name) end
function W.done() L.dump_ppu("final"); done() end
