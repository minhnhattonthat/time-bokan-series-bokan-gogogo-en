"""Run scenes of tools/debug/scenes.lua from cold boot, each in work/qa/warp/<scene>; exit 1 if any fails.

    python -X utf8 tools/debug/warp_all.py [--rom CUE] [--jobs 3] [--out DIR] [--states] [--list] [scene ...]

--states also saves work/states/<scene>.sstate. A shot is judged by a flat-colour test on final.png (emu.py --smoke);
the state checks inside each scene fail the run on their own (exit 2 from emu.py).
"""
import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

DEFAULT_ROM = os.path.join(ROOT, "rom", "Time Bokan Series - Bokan GoGoGo (Japan).cue")
SCENES = os.path.join(ROOT, "tools", "debug", "scenes.lua")
WARP = os.path.join(ROOT, "tools", "debug", "warp.lua")
LONG = {}  # scene -> frame budget when 20000 is not enough
NO_SMOKE = set()  # scenes that end on a flat colour by design


def scene_names():
    """Names of the scene list: every `S.<name> = ` line and every `S["<name>"] = ` generated in a loop."""
    src = open(SCENES, encoding="utf-8").read()
    names = re.findall(r"^S\.(\w+) = ", src, re.M)
    for m in re.finditer(r"^-- names: (.+)$", src, re.M):
        names += m.group(1).split()
    return names


def run(scene, rom, out, states, extra):
    d = os.path.join(out, scene)
    frames = LONG.get(scene, 20000)
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), rom, "--out", d, "--frames", str(frames),
           "--timeout", "1200", "--script", WARP, "--script", SCENES, "--var", f"SCENE='{scene}'"] + extra
    if scene not in NO_SMOKE:
        cmd.append("--smoke")
    if states:
        cmd += ["--state-out", os.path.join(ROOT, "work", "states", scene + ".sstate")]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    log = os.path.join(d, "log.txt")
    last = ""
    if os.path.exists(log):
        lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
        last = lines[-1] if lines else ""
    return scene, r.returncode, last, r.stdout.strip().splitlines()[-2:] if r.returncode else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default=DEFAULT_ROM)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "warp"))
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--script", action="append", default=[], help="extra Lua after scenes.lua")
    ap.add_argument("scenes", nargs="*")
    a = ap.parse_args()
    names = a.scenes or scene_names()
    if a.list:
        print("\n".join(names))
        return 0
    extra = [x for s in a.script for x in ("--script", os.path.abspath(s))]
    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for scene, rc, last, err in ex.map(lambda s: run(s, a.rom, a.out, a.states, extra), names):
            print(f"{'ok  ' if rc == 0 else 'FAIL'} {scene:18} rc={rc} {last} {err}", flush=True)
            bad += rc != 0
    print(f"{len(names) - bad}/{len(names)} scenes ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
