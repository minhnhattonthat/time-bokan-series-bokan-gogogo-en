"""Phase 1 findings held as tests: disc layout, TIMP format, and the only Shift-JIS text (docs/re/)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import disc  # noqa: E402
import tim  # noqa: E402
import timp  # noqa: E402

BIN = ROOT / "rom" / "Time Bokan Series - Bokan GoGoGo (Japan).bin"
pytestmark = pytest.mark.skipif(not BIN.is_file(), reason="no dump in rom/")


@pytest.fixture(scope="module")
def d():
    return disc.Disc(str(BIN))


def test_layout(d):
    files = d.files
    assert "/SLPS_031.33" in files and "/OVER/DEMO.BIN" in files
    assert sum(p.startswith("/STR/") for p in files) == 19  # BOGO01-18 + STAFF
    assert sum(p.endswith(".TMP") for p in files) == 197


def test_timp_grap_decodes_to_tims(d):
    """Every GRAP archive entry is a TIM (MODE1.TMP is plain TIMs, not TIMP)."""
    n = 0
    for p in sorted(f for f in d.files if f.startswith("/GRAP/") and f.endswith(".TMP")):
        data = d.read(p)
        if p == "/GRAP/MODE1.TMP":
            assert data[:4] == b"\x10\0\0\0"
            continue
        for b in timp.unpack(data):
            assert tim.parse(b, strict=False), p
            n += 1
    assert n == 1493


def test_timp_identity_and_store(d):
    data = d.read("/GRAP/TITLE.TMP")
    blobs = timp.unpack(data)
    comp = [data[o:o + c] for o, _, c in timp.entries(data)]
    assert timp.pack(blobs, comp) == data
    stored = timp.pack(blobs)
    assert timp.unpack(stored) == blobs


def test_only_sjis_is_memory_card_titles(d):
    demo = d.read("/OVER/DEMO.BIN")
    title = "ボカンＧＯＧＯＧＯ".encode("cp932")
    assert demo.count(title) == 33  # 1 plain + 16 courses x 2 files
    assert title not in d.read("/SLPS_031.33")
