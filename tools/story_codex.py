"""Story-pass verdicts by `codex exec` (read-only), one run per chapter, since Orca refuses nested subagents.

usage: story_codex.py CHAPTER.txt.. [--jobs 3] [--tag fixed]
Each run gets docs/story-reviewer-brief.md and one chapter file (tools/pairs.py --chapters); its report goes to
work/qa/story/reports/<chapter>.txt and `<chapter><TAB>ok|issue<TAB>note` (from its Assessment) to
work/qa/story/verdicts/<chapter>[_<tag>].tsv. --tag (e.g. fixed, fixed2) writes a newer file for a re-review after
fixes and maps ok to `fixed`. Exit 1 if a report has no Assessment."""
import concurrent.futures as cf
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "work" / "qa" / "story"


def run(chapter, tag):
    rel = Path(chapter).resolve().relative_to(ROOT).as_posix()
    name = Path(chapter).stem
    raw = STORY / "reports" / (name + (f"_{tag}" if tag else "") + ".txt")
    prompt = (f"You are a read-only story reviewer. Follow docs/story-reviewer-brief.md (read it first, then"
              f" docs/synopsis.md, docs/style-reference.md, glossary.md and docs/decisions.md D12). Your chapter file is"
              f" {rel}: read all of it. Lines whose note starts with `?` are transcription guesses from audio nobody"
              f" has heard; judge the English against the Japanese as written. Your final message is the report in the"
              f" brief's format, ending with a line `Assessment: ok` or `Assessment: issue - <why>`.\n")
    cmd = [shutil.which("codex"), "exec", "-s", "read-only", "-C", str(ROOT), "-o", str(raw), "--", "-"]
    # prompt on stdin: codex is a .cmd shim on Windows, which mangles newlines in arguments
    with open(raw.with_suffix(".log"), "w", encoding="utf-8") as log:
        subprocess.run(cmd, input=prompt, stdout=log, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    text = raw.read_text(encoding="utf-8") if raw.exists() else ""
    m = re.findall(r"Assessment:?\**\s*`?(ok|issue)`?\s*[-:]?\s*(.*)", text, re.I)
    if not m:
        return name, None
    word, note = m[-1][0].lower(), m[-1][1].strip()
    word = "fixed" if (tag and word == "ok") else word
    (STORY / "verdicts" / (name + (f"_{tag}" if tag else "") + ".tsv")).write_text(
        f"{name}\t{word}\t{note}\n", encoding="utf-8")
    return name, word


if __name__ == "__main__":
    a = sys.argv[1:]
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 3
    tag = a[a.index("--tag") + 1] if "--tag" in a else ""
    files = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--jobs", "--tag"))]
    (STORY / "reports").mkdir(parents=True, exist_ok=True)
    (STORY / "verdicts").mkdir(parents=True, exist_ok=True)
    bad = 0
    with cf.ThreadPoolExecutor(jobs) as ex:
        for name, word in ex.map(lambda c: run(c, tag), files):
            print(f"{name}: {word or 'NO ASSESSMENT'}", flush=True)
            bad += word is None
    sys.exit(1 if bad else 0)
