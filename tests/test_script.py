"""Phase 4: every TIM on the disc is either text (its blob has rows in script/graphics.tsv) or listed in
script/no_text.txt, never both; rects hold ink; the save titles roundtrip through tbl/save.tbl; movie scripts are
cleaned and in time order; the credit roll's cast groups are well formed."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import disc  # noqa: E402
import gfx_index  # noqa: E402
import gfx_script  # noqa: E402
import gfx_sheet  # noqa: E402
import save_titles  # noqa: E402
from tbl import Table  # noqa: E402

BIN = build.ROM / build.BIN
needs_rom = pytest.mark.skipif(not BIN.exists(), reason="needs the dump in rom/")


@pytest.fixture(scope="module")
def tims():
    return gfx_index.tims()


def test_gfx_rows_are_unique_and_complete():
    rows = gfx_script.rows()
    ids = [r.id for r in rows]
    assert len(ids) == len(set(ids))
    assert all(r.jp and r.w > 0 and r.h > 0 and r.form for r in rows)


@needs_rom
def test_every_tim_is_accounted_for_once(tims):
    idx = gfx_index.index(tims)
    sha = {i: h for i, h, _, _ in idx}
    canon = {i: c for i, _, _, c in idx}
    counts = {}
    for i, _ in tims:
        counts[i.split("#")[0]] = counts.get(i.split("#")[0], 0) + 1
    text_files = {r.file for r in gfx_script.rows()}
    assert all(canon[f] == f for f in text_files), "graphics.tsv must name the canonical copy"
    text_hashes = {sha[f] for f in text_files}
    listed = gfx_script.no_text(archives=counts)
    assert listed <= set(sha), listed - set(sha)
    for i in sha:
        assert (sha[i] in text_hashes) != (i in listed), i
    assert len(tims) == 12209


@needs_rom
def test_gfx_rects_hold_ink(tims):
    blob = dict(tims)
    for r in gfx_script.rows():
        img = gfx_sheet.render(blob[r.file])
        assert r.x >= 0 and r.y >= 0 and r.x + r.w <= img.width and r.y + r.h <= img.height, r.id
        assert img.crop((r.x, r.y, r.x + r.w, r.y + r.h)).getchannel("A").getbbox(), f"{r.id} is blank"


@needs_rom
def test_save_titles_roundtrip():
    demo = disc.Disc(str(BIN)).read(save_titles.FILE)
    t = Table.load(save_titles.TBL)
    rows = save_titles.rows()
    fields = save_titles.fields(demo)
    assert len(rows) == len(fields) == 33
    for (n, off, jp, en), (o, b) in zip(rows, fields):
        assert int(off, 16) == o
        assert save_titles.decode(t, b) == jp
        assert save_titles.encode(t, jp) == b
        assert save_titles.decode(t, save_titles.encode(t, en)) == en  # D8: full width, fits the field


@needs_rom
def test_english_save_titles_land_in_their_fields():
    demo = disc.Disc(str(BIN)).read(save_titles.FILE)
    new = save_titles.english(demo)
    t = Table.load(save_titles.TBL)
    assert len(new) == len(demo)
    assert [save_titles.decode(t, b) for _, b in save_titles.fields(new)] == [r[3] for r in save_titles.rows()]
    spans = [(o, o + save_titles.FIELD) for o, _ in save_titles.fields(demo)]
    outside = [i for i in range(len(demo)) if demo[i] != new[i] and not any(a <= i < b for a, b in spans)]
    assert not outside


def test_fmv_scripts_in_time_order():
    files = sorted((ROOT / "script" / "fmv").glob("*.tsv"))
    assert [f.stem for f in files] == [f"BOGO{n:02d}" for n in range(1, 19)]
    for f in files:
        last = 0.0
        for ln in f.read_text(encoding="utf-8").splitlines()[1:]:
            start, end, form, speaker, jp, en, *note = ln.split("\t")
            assert form in ("dlg", "song", "caption"), ln
            assert last <= float(start) < float(end), ln
            assert not (note and note[0].startswith("draft")), ln  # every file is cleaned
            if form == "song":
                assert not jp and not en, ln  # D9: lyrics stay out of git, no subtitles
            else:
                assert jp and speaker and not re.search(r"[A-Za-z]{4}", jp), ln
                assert en and en.isascii(), ln
            last = float(start)


def en_pairs():
    """(where, speaker, jp, en) for every graphics row, movie line and credit line."""
    jp = {r.id: r.jp for r in gfx_script.rows()}
    out = [(rid, "", jp[rid], en) for rid, en, *_ in
           (ln.split("\t") for ln in (ROOT / "script" / "graphics_en.tsv").read_text(encoding="utf-8").splitlines()[1:])]
    for f in sorted((ROOT / "script" / "fmv").glob("*.tsv")):
        for ln in f.read_text(encoding="utf-8").splitlines()[1:]:
            c = ln.split("\t")
            if c[5]:
                out.append((f"{f.stem}@{c[0]}", c[3], c[4], c[5]))
    for c in (ln.split("\t") for ln in (ROOT / "script" / "credits.tsv").read_text(encoding="utf-8").splitlines()[1:]):
        out.append((f"credits#{c[0]}", "", c[3], c[4]))
    return out


def glossary():
    """(jp alternatives, en alternatives, avoid list) from every table in glossary.md."""
    terms = []
    for ln in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if not ln.startswith("|") or len(c) < 5 or c[0] in ("JP", "---"):
            continue
        avoid = [a.split("(")[0].strip() for a in c[4].split(",") if a.strip()]
        terms.append(([j.strip() for j in c[0].split("/")], [e.strip() for e in c[1].split("/")], avoid))
    return terms


# jp present, en form deliberately reworded (where -> why)
GLOSSARY_WAIVED = {
    "MODE#145": "movie tab, 46 px: Punishment",
    "BOGO07@7.32": "the other trios: villains already named by context",
    "BOGO18@13.74": "the other trios: Dokurobey speaks of the villains",
}


def has_term(low, en):
    """en form found, ignoring '(s)', a trailing '!' and case."""
    return en.lower().replace("(s)", "").split(" (")[0].rstrip("!") in low


def test_glossary_and_charset():
    """translation.md §Validation: Avoid spellings, glossary terms, honorifics (D1), Dokurobey's tic, ASCII."""
    bad = []
    terms = glossary()
    for where, speaker, jp, en in en_pairs():
        low = en.lower()
        if not all(ch.isascii() or ch == "©" for ch in en):
            bad.append((where, "non-ASCII", en))
        for jps, ens, avoid in terms:
            bad += [(where, f"avoid {a}", en) for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
            hit = next((j for j in jps if j and j in jp), None)
            if hit and not any(has_term(low, e) for e in ens) and where not in GLOSSARY_WAIVED:
                bad.append((where, f"{hit} without {ens}", en))
        if re.search(r"(?<![仕模])様(?!子)", jp) and "-sama" not in en and where not in GLOSSARY_WAIVED:
            bad.append((where, "様 without -sama", en))
        if "さん" in jp and "-san" not in en and where not in GLOSSARY_WAIVED:
            bad.append((where, "さん without -san", en))
        if (speaker == "Dokurobey" or where.startswith("DOKURO#")) and re.search(r"べ[ェエー]?[。！!…]*$", jp) \
                and "y'hear" not in en:
            bad.append((where, "Dokurobey's tic missing", en))
    assert not bad, "\n".join(map(str, bad))


def test_credits_rows():
    rows = [ln.split("\t") for ln in (ROOT / "script" / "credits.tsv").read_text(encoding="utf-8").splitlines()[1:]]
    assert [int(r[0]) for r in rows] == list(range(1, len(rows) + 1))
    groups = [int(r[1]) for r in rows]
    assert groups == sorted(groups)
    for r in rows:
        assert r[2] in ("head", "sub", "name", "role", "actor") and r[3], r
        assert r[4] and r[4].isascii(), r  # en, Western name order (D1)
    for g in set(groups):  # a cast group is roles then one actor
        kinds = [r[2] for r in rows if int(r[1]) == g]
        if "actor" in kinds:
            assert kinds[-1] == "actor" and set(kinds[:-1]) == {"role"}, g
