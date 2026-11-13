"""Turn fmv_transcribe.py's Whisper output into draft movie scripts: script/fmv/<movie>.tsv
(start, end, form, speaker, jp, note). Every row is marked `draft` with Whisper's avg_logprob and no_speech_prob,
for the cleaning pass (names, mishearings, lines invented over music) to correct or drop. Never overwrites a file
that has lost its `draft` marks unless --force.

usage: fmv_draft.py WHISPER_DIR [--movies BOGO02 ...] [--force]"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "script" / "fmv"


def draft(src):
    rows, last = ["start\tend\tform\tspeaker\tjp\tnote"], -1.0
    for ln in src.read_text(encoding="utf-8").splitlines():
        start, end, lp, ns, text = ln.split("\t", 4)
        s, e = max(float(start), last + 0.01), float(end)
        if not text.strip():
            continue
        rows.append(f"{s:.2f}\t{max(e, s + 0.01):.2f}\tdlg\t\t{text.strip()}\tdraft lp {lp} ns {ns}")
        last = s
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("whisper")
    ap.add_argument("--movies", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for src in sorted(Path(a.whisper).glob("*.whisper.tsv")):
        name = src.name.split(".")[0]
        if a.movies and name not in a.movies:
            continue
        dst = OUT / f"{name}.tsv"
        if dst.exists() and "\tdraft" not in dst.read_text(encoding="utf-8") and not a.force:
            sys.exit(f"{dst} is cleaned; --force to overwrite")
        dst.write_text(draft(src), encoding="utf-8", newline="\n")
        print(dst.name, dst.read_text(encoding="utf-8").count("\n") - 1, "rows")
