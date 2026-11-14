"""Second Whisper pass for the movie cleaning: re-transcribe each row of script/fmv/<movie>.tsv as its own clip
(0.3 s padding), with an initial prompt of series names, so each row gets a second reading to compare with the
first. The prompt is safe here (fmv_transcribe.py's warning was about whole movies with long music lead-ins).

usage: fmv_pass2.py WAV_DIR OUT_DIR [--movies BOGO02 ...]
Writes OUT_DIR/<movie>.pass2.tsv: start, end, avg_logprob, no_speech_prob, text (one line per script row)."""
import argparse
import os
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
# names from the MODE#115-180 sprites (script/graphics.tsv) plus the heroes' sidekicks
PROMPT = ("ドクロベエ様、ドロンジョ、ボヤッキー、トンズラー、マージョ、グロッキー、ワルサー、ムージョ、トンメンタン、"
          "トボッケー、アターシャ、セコビッチ、ドワルスキー、ミレンジョ、コスイネン、スカドン、ムンムン、キョカンチン、"
          "コケマツ、ヤンヤン、ダサイネン、ドンジューロー、ヤッターマン、ガンちゃん、アイちゃん、オモッチャマ、"
          "ゼンダマン、丹平、淳子、ルージュ、ヒエール、オンドレー、きらめきマン、タイムボカン、主役の座、だべ。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wavs")
    ap.add_argument("out")
    ap.add_argument("--movies", nargs="*")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
    for tsv in sorted((ROOT / "script" / "fmv").glob("*.tsv")):
        if a.movies and tsv.stem not in a.movies:
            continue
        with wave.open(os.path.join(a.wavs, tsv.stem + ".wav")) as w:
            rate = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        out = []
        for ln in tsv.read_text(encoding="utf-8").splitlines()[1:]:
            s, e = (float(x) for x in ln.split("\t")[:2])
            clip = pcm[int(max(0, s - 0.3) * rate):int((e + 0.3) * rate)]
            segs, _ = model.transcribe(clip, language="ja", vad_filter=False, beam_size=5, initial_prompt=PROMPT,
                                       condition_on_previous_text=False, no_speech_threshold=None)
            segs = list(segs)
            text = "".join(x.text.strip() for x in segs)
            lp = min((x.avg_logprob for x in segs), default=0.0)
            ns = max((x.no_speech_prob for x in segs), default=1.0)
            out.append(f"{s:.2f}\t{e:.2f}\t{lp:.2f}\t{ns:.2f}\t{text}")
        Path(a.out, tsv.stem + ".pass2.tsv").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
        print(tsv.stem, "done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
