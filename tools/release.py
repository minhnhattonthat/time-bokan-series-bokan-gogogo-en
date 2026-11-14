"""Release gate and packager (pipeline.md §Release). Stops at the first failing step.

usage: release.py VERSION [--force]      e.g. release.py 1.0
Uses the built disc in build/en/ (`tools/build.py --en`, ~30 min; not rebuilt here, the QA manifests pin its hash):
  dump hash -> tests -> smoke -> discdiff (only allowed files changed, SLPS_031.33 untouched = no debug code)
  -> jp_left (DEMO.BIN --sjis, SLPS_031.33 --known) -> qa_gate check on every work/qa/**/manifest.tsv
  -> textcover -> docs/polish.md all ticked -> README.md has no template placeholder
  -> xdelta3 patch -> re-applied to the original and compared -> release/<name>_vVERSION.zip (patch + README.txt).
Refuses to overwrite an existing version's files without --force. Never publishes anything."""
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import disc  # noqa: E402
from skill import SKILL  # noqa: E402

NAME = "Time Bokan Series - Bokan GoGoGo (Japan)"
ORIG, BUILT = ROOT / "rom" / f"{NAME}.bin", ROOT / "build" / "en" / f"{NAME}.bin"
SLUG = "Time_Bokan_Series_Bokan_GoGoGo_EN"
PY = [sys.executable, "-X", "utf8"]
PLACEHOLDER = re.compile(r"<(Game title|platform|publisher|year|repo|file|size|sha1|game|ext|Translated|Left in|"
                         r"none known|Dialogue|Menus|Title screen|Name entry|Songs)[^>]*>")


def step(name, cmd=None, ok=None):
    print(f"== {name}", flush=True)
    if cmd is not None:
        r = subprocess.run(cmd, cwd=ROOT)
        ok = r.returncode == 0
    if not ok:
        sys.exit(f"release stopped: {name} failed")


def hashes(path):
    h = {"sha1": hashlib.sha1(), "md5": hashlib.md5()}
    crc, size = 0, 0
    with open(path, "rb") as f:
        while b := f.read(1 << 22):
            for x in h.values():
                x.update(b)
            crc, size = zlib.crc32(b, crc), size + len(b)
    return {"size": size, "crc32": f"{crc:08X}", **{k: v.hexdigest() for k, v in h.items()}}


def main(version, force):
    out = ROOT / "release"
    zpath, patch = out / f"{SLUG}_v{version}.zip", out / f"{SLUG}_v{version}.xdelta"
    if (zpath.exists() or patch.exists()) and not force:
        sys.exit(f"{zpath.name} exists: pass --force to overwrite")
    step("dump", PY + ["tools/check_rom.py"])
    step("built disc present", ok=BUILT.exists())
    step("tests", PY + ["tools/check.py"])
    step("smoke", PY + [f"{SKILL}/scripts/emu.py", str(BUILT.with_suffix(".cue")), "--out", "work/qa/release_smoke",
                        "--route", "tools/routes/boot.txt", "--smoke"])
    step("discdiff", PY + ["tools/discdiff.py", str(ORIG), str(BUILT), "script/allowed.txt"])
    o, b = disc.Disc(str(ORIG)), disc.Disc(str(BUILT))
    exe = next(p for p in o.files if "SLPS" in p)
    step("no code changes (debug tool is Lua only)", ok=o.read(exe) == b.read(exe))
    with tempfile.TemporaryDirectory() as tmp:
        demo, slps = Path(tmp) / "DEMO.BIN", Path(tmp) / "SLPS.BIN"
        demo.write_bytes(b.read(next(p for p in b.files if p.endswith("DEMO.BIN"))))
        slps.write_bytes(b.read(exe))
        step("jp_left DEMO.BIN", PY + [f"{SKILL}/scripts/jp_left.py", str(demo), "--sjis"])
        step("jp_left SLPS", PY + [f"{SKILL}/scripts/jp_left.py", str(slps), "--sjis", "--known", "script/jp_known.txt"])
    manifests = sorted((ROOT / "work" / "qa").rglob("manifest.tsv"))
    step("QA manifests found", ok=len(manifests) >= 2)
    for m in manifests:
        step(f"qa_gate {m.relative_to(ROOT).as_posix()}",
             PY + [f"{SKILL}/scripts/qa_gate.py", "check", str(m), str(m.parent / "verdicts")])
    step("textcover", PY + [f"{SKILL}/scripts/textcover.py", "work/qa/env_cover", "work/qa/env_cover/strings.tsv",
                            "--waive", "docs/text_unshown.tsv"])
    open_lines = [ln for ln in (ROOT / "docs" / "polish.md").read_text(encoding="utf-8").splitlines()
                  if ln.lstrip().startswith("- [ ]")]
    step(f"polish.md ticked ({len(open_lines)} open)", ok=not open_lines)
    step("README.md placeholders", ok=not PLACEHOLDER.search((ROOT / "README.md").read_text(encoding="utf-8")))

    out.mkdir(exist_ok=True)
    base, new = hashes(ORIG), hashes(BUILT)
    patch.unlink(missing_ok=True)
    step("xdelta3 encode", [shutil.which("xdelta3"), "-e", "-9", "-f", "-B", str(base["size"]), "-s", str(ORIG),
                            str(BUILT), str(patch)])
    with tempfile.TemporaryDirectory() as tmp:
        re_bin = Path(tmp) / "patched.bin"
        step("xdelta3 apply", [shutil.which("xdelta3"), "-d", "-f", "-B", str(base["size"]), "-s", str(ORIG),
                               str(patch), str(re_bin)])
        step("re-applied patch equals the build", ok=hashes(re_bin)["sha1"] == new["sha1"])
    readme = (ROOT / "docs" / "release_readme.txt").read_text(encoding="utf-8").format(
        version=version, patch=patch.name, name=NAME, **{f"base_{k}": v for k, v in base.items()},
        **{f"new_{k}": v for k, v in new.items()}, patch_sha1=hashes(patch)["sha1"])
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:  # xdelta is already compressed
        z.write(patch, patch.name)
        z.writestr("README.txt", readme.replace("\n", "\r\n"))
    print(f"ok: {zpath} ({zpath.stat().st_size:,} bytes), patch sha1 {hashes(patch)['sha1']}, "
          f"patched bin sha1 {new['sha1']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help") or a[0].startswith("-"):
        sys.exit(__doc__)
    main(a[0], "--force" in a)
