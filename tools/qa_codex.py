"""Visual-QA verdicts by `codex exec` (read-only), one run per qa_gate chunk, since Orca refuses nested subagents.

usage: qa_codex.py CHUNK.txt.. [--jobs 3]     (chunks from qa_gate.py todo --out-dir work/qa/chunks)
Each run gets docs/visual-qa-brief.md, its sheets attached as images (-i) and the Japanese sheet paths; its last
message goes to work/qa/verdicts_raw/<chunk>.txt, and its `id<TAB>ok|issue<TAB>note` lines for ids in the chunk to
work/qa/verdicts/<chunk>.tsv. Exit 1 if any chunk has an id without a verdict."""
import concurrent.futures as cf
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "work" / "qa" / "verdicts_raw", ROOT / "work" / "qa" / "verdicts"


def prompt(rows):
    lst = "\n".join(f"{i}\t{p}\tJapanese: work/qa/sheets_jp/{Path(p).name}" for i, p in rows)
    return (f"You are a read-only visual-QA reviewer. Follow docs/visual-qa-brief.md (read it first; also glossary.md)."
            f" You cannot write files: instead, your FINAL message must be only the verdict lines, one per id below,"
            f" `id<TAB>ok|issue<TAB>note`, then nothing else. The sheets are attached in this order; open the Japanese"
            f" sheet or a single shot under work/qa/env/<scene>/ with your image viewer when something looks wrong."
            f" Read every sheet; every id needs a line.\n\n{lst}\n")


def run(chunk):
    rows = [ln.split("\t") for ln in Path(chunk).read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows = [(r[0], r[-1]) if len(r) > 1 else (Path(r[0]).stem, r[0]) for r in rows]
    raw = RAW / (Path(chunk).stem + ".txt")
    cmd = [shutil.which("codex"), "exec", "-s", "read-only", "-C", str(ROOT), "-o", str(raw)]
    for _, p in rows:
        cmd += ["-i", str(ROOT / p)]
    # prompt on stdin ("-"): codex is a .cmd shim on Windows, which mangles newlines and tabs in arguments
    with open(raw.with_suffix(".log"), "w", encoding="utf-8") as log:
        subprocess.run(cmd + ["--", "-"], input=prompt(rows), stdout=log, stderr=subprocess.STDOUT, text=True,
                       encoding="utf-8")
    ids = {i for i, _ in rows}
    text = raw.read_text(encoding="utf-8") if raw.exists() else ""
    got = {}
    for ln in text.splitlines():
        m = re.match(r"^`?([\w-]+)`?\t(ok|issue)\t?(.*)$", ln.strip())
        if m and m.group(1) in ids:
            got[m.group(1)] = (m.group(2), m.group(3).strip())
    (OUT / (Path(chunk).stem + ".tsv")).write_text("".join(f"{i}\t{v}\t{n}\n" for i, (v, n) in got.items()),
                                                    encoding="utf-8")
    return chunk, len(ids), len(got), sum(v == "issue" for v, _ in got.values())


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 3
    args = [a for a in args if not a.isdigit()]
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    with cf.ThreadPoolExecutor(jobs) as ex:
        for chunk, n, got, issues in ex.map(run, args):
            print(f"{Path(chunk).name}: {got}/{n} verdicts, {issues} issues", flush=True)
            bad += got < n
    sys.exit(1 if bad else 0)
