"""Debug tool pieces that run without the emulator: the blank memory card and the scene list."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "debug"))
import warp_all  # noqa: E402


def test_blank_card_is_formatted():
    d = warp_all.blank_card()
    assert len(d) == 0x20000 and d[:2] == b"MC" and d[63 * 128:63 * 128 + 2] == b"MC"
    for i in range(64):
        f = d[i * 128:(i + 1) * 128]
        x = 0
        for b in f[:127]:
            x ^= b
        assert f[127] == x, f"frame {i} checksum"
    assert all(d[i * 128] == 0xA0 for i in range(1, 16))  # 15 free blocks


def test_scene_names_unique():
    names = warp_all.scene_names()
    assert len(names) == len(set(names))
    assert {"race_results", "story_saved", "race_c7"} <= set(names)
