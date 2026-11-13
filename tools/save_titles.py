"""The 33 memory-card save titles in OVER/DEMO.BIN (docs/re/text.md): Shift-JIS, full width, FIELD bytes each,
padded with U+3000 (8140), STRIDE apart from BASE. Only the BIOS card manager shows them.

usage: save_titles.py extract     write script/save_titles.tsv (n, offset, jp without the pad) and tbl/save.tbl
`decode`/`encode` go through tbl/save.tbl, so the roundtrip test proves every byte maps to a table entry."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table

FILE, BASE, STRIDE, FIELD, COUNT = "/OVER/DEMO.BIN", 0xBC8, 0x44, 64, 33
PAD = "　"
TSV, TBL = ROOT / "script" / "save_titles.tsv", ROOT / "tbl" / "save.tbl"


def fields(demo):
    return [(BASE + n * STRIDE, demo[BASE + n * STRIDE:BASE + n * STRIDE + FIELD]) for n in range(COUNT)]


def decode(t, b):
    text, used = t.decode(b, 0, length=FIELD)
    assert used == FIELD
    return text.rstrip(PAD)


def encode(t, text):
    b = t.encode(text)
    assert len(b) <= FIELD and len(b) % 2 == 0, (text, len(b))
    return b + t.encode(PAD) * ((FIELD - len(b)) // 2)


def rows():
    return [ln.split("\t") for ln in TSV.read_text(encoding="utf-8").splitlines()[1:]]


def extract():
    assert not TSV.exists() or "en" not in TSV.read_text(encoding="utf-8").split("\n", 1)[0].split("\t"), \
        "script/save_titles.tsv has the English column; extract would drop it"
    import build
    import disc
    demo = disc.Disc(str(build.ROM / build.BIN)).read(FILE)
    chars = sorted({c for _, b in fields(demo) for c in b.decode("cp932")})
    TBL.parent.mkdir(exist_ok=True)
    TBL.write_text("# Shift-JIS characters of the save titles (save_titles.py)\n"
                   + "".join(f"{c.encode('cp932').hex().upper()}={c}\n" for c in chars), encoding="utf-8", newline="\n")
    t = Table.load(TBL)
    with open(TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("n\toffset\tjp\n")
        for n, (off, b) in enumerate(fields(demo)):
            f.write(f"{n}\t{off:#x}\t{decode(t, b)}\n")
    print(COUNT, "titles,", len(chars), "characters")


def english(demo):
    """DEMO.BIN with every title replaced by its `en` column (D8), each in its own 64-byte field."""
    t = Table.load(TBL)
    out = bytearray(demo)
    for (n, off, jp, en), (o, b) in zip(rows(), fields(demo)):
        assert int(off, 16) == o and decode(t, b) == jp, n
        out[o:o + FIELD] = encode(t, en)
    return bytes(out)


def patch(track):
    """build.py --en: the English titles into the built disc."""
    import disc
    d = disc.Disc(str(track), write=True)
    d.write_file(FILE, english(d.read(FILE)))
    d.f.close()


if __name__ == "__main__":
    extract()
