"""Identity build (phase 3): rom/ through the whole build path, with no edits, must come out byte-identical."""
import hashlib
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import disc  # noqa: E402
import timp  # noqa: E402

needs_rom = pytest.mark.skipif(not (build.ROM / build.BIN).exists(), reason="needs the dump in rom/")


@pytest.fixture(scope="module")
def built_bin(tmp_path_factory):
    out = tmp_path_factory.mktemp("build")
    calls = []
    write, rebuild = disc.Disc.write_file, build.rebuild_timp
    disc.Disc.write_file = lambda self, p, b: (calls.append(p), write(self, p, b))
    build.rebuild_timp = lambda data: (calls.append(timp.MAGIC), rebuild(data))[1]
    try:
        build.build(out, identity=True)
    finally:
        disc.Disc.write_file, build.rebuild_timp = write, rebuild
    d = disc.Disc(str(build.ROM / build.BIN))
    # not vacuous: every form 1 file was rewritten and every TIMP archive went through unpack/pack
    assert set(calls) - {timp.MAGIC} == {p for p, e in d.files.items() if not d.is_xa(e)}
    assert calls.count(timp.MAGIC) == 196
    return out / build.BIN


@needs_rom
def test_identity_build_matches_the_dump(built_bin):
    want = next(ln.split()[0] for ln in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if build.BIN in ln)
    with open(built_bin, "rb") as f:
        assert hashlib.file_digest(f, "sha1").hexdigest() == want


@needs_rom
def test_an_edited_timp_entry_lands_and_the_rest_keep_their_bytes():
    """Guards against a vacuous identity: an edited entry is re-stored and reads back; the others are unchanged."""
    data = disc.Disc(str(build.ROM / build.BIN)).read("/GRAP/GOVER.TMP")
    new = build.rebuild_timp(data, lambda i, b: b[:-1] + bytes([b[-1] ^ 1]) if i == 0 else b)
    old, got = timp.unpack(data), timp.unpack(new)
    assert got[0] != old[0] and got[0][:-1] == old[0][:-1] and got[1:] == old[1:]
    comp = lambda b: [b[o:o + c] for o, _, c in timp.entries(b)]  # noqa: E731
    assert comp(new)[1:] == comp(data)[1:]  # untouched entries keep their BPE bytes
    assert timp.pack(old, comp(data), timp.align_of(data)) == data


def test_align_of_needs_a_gap():
    a, b = b"x" * 4, b"y" * 4  # aligned by chance, no padding: packed layout
    assert timp.align_of(timp.pack([a, b], [a, b], 1)) == 1
    assert timp.align_of(timp.pack([a, b], [b"x" * 3, b], 4)) == 4
    with pytest.raises(AssertionError):
        timp.pack([a, b], [a])


@needs_rom
def test_discdiff_flags_unallowed_files_and_subheaders(built_bin, tmp_path):
    import discdiff
    copy = tmp_path / "d.bin"
    shutil.copyfile(built_bin, copy)
    d = disc.Disc(str(build.ROM / build.BIN))
    cnf, demo = d.files["/SYSTEM.CNF"].lba, d.files["/OVER/DEMO.BIN"].lba
    with open(copy, "r+b") as f:
        for off in (cnf * disc.SECTOR + disc.USER, demo * disc.SECTOR + 18, demo * disc.SECTOR + 600):
            f.seek(off)
            b = f.read(1)
            f.seek(off)
            f.write(bytes([b[0] ^ 1]))
    errs, per = discdiff.check(build.ROM / build.BIN, copy, {"/OVER/DEMO.BIN"})
    assert any("SYSTEM.CNF" in e and "not allowed" in e for e in errs)
    assert any("DEMO.BIN" in e and "subheader" in e for e in errs)
    assert len(errs) == 2 and per == {"/OVER/DEMO.BIN": 1}
    assert discdiff.check(build.ROM / build.BIN, copy, {"/OVER/DEMO.BIN", "/SYSTEM.CNF"})[0] == [e for e in errs if "DEMO" in e]


@needs_rom
def test_tim_errors_flags_stray_and_missed_writes():
    import tim
    blobs = timp.unpack(disc.Disc(str(build.ROM / build.BIN)).read("/GRAP/GOVER.TMP"))
    a, b = blobs[0], next(x for x in blobs if x != blobs[0])
    flip = lambda x, o: x[:o] + bytes([x[o] ^ 1]) + x[o + 1:]  # noqa: E731
    ed = flip(a, len(a) - 1)
    edits = {hashlib.sha1(a).hexdigest(): lambda x: ed}
    orig = [("G#0", a), ("G#1", a), ("G#2", b)]
    assert build.tim_errors(orig, [("G#0", ed), ("G#1", ed), ("G#2", b)], edits) == []
    hdr = tim.parse(a, strict=False).px_off - 1  # last byte before the pixels: pixel-block header
    errs = build.tim_errors(orig, [("G#0", flip(ed, hdr)), ("G#1", a), ("G#2", flip(b, len(b) - 1))], edits)
    assert errs == ["G#0: not its edit's output", "G#0: TIM header, CLUT or size changed",
                    "G#1: original copy of an edited blob left", "G#2: unedited TIM changed"]
    assert build.tim_errors(orig, orig[:2], edits)


@needs_rom
def test_english_edits_stay_in_the_committed_allowed_list():
    import gfx
    assert build.allowed_files(gfx.spike_edits(gfx.EN)) <= build.allowed_spec()


@needs_rom
def test_write_file_changes_only_that_file(built_bin, tmp_path):
    copy = tmp_path / "t.bin"
    shutil.copyfile(built_bin, copy)
    d = disc.Disc(str(copy), write=True)
    e = d.files["/SYSTEM.CNF"]
    old = d.read(e.path)
    new = bytes([old[0] ^ 1]) + old[1:]
    d.write_file(e.path, new)
    assert d.read(e.path) == new
    d.f.close()
    a, b = built_bin.read_bytes(), copy.read_bytes()
    start, end = e.lba * disc.SECTOR, (e.lba + 1) * disc.SECTOR
    assert a[:start] == b[:start] and a[end:] == b[end:] and a[start:end] != b[start:end]
    sec = bytearray(b[start:end])
    disc.form1_seal(sec)
    assert sec == bytearray(b[start:end])  # EDC/ECC of the changed sector are valid
