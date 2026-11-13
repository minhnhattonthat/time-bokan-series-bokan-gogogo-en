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
    build.build(out, identity=True)
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
    assert timp.pack(old, [data[o:o + c] for o, _, c in timp.entries(data)], timp.align_of(data)) == data


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
