"""List every write of the main state M (8003DEE4, `sw $v0, -0x211c($at)` after `lui $at, 0x8004`) in a disassembly
listing (work/*.dis from disasm.py), with the constant stored when it is set within the 12 lines before.

    python -X utf8 tools/mwrites.py work/demo.dis [work/cart.dis ...] [--value 0x23]
"""
import argparse
import re

STORE = re.compile(r"^([0-9A-F]{8}) .*\bsw\s+\$(\w+), -0x211c\(\$at\)")
CONST = r"addiu\s+\${reg}, \$zero, (0x[0-9a-f]+|\d+)\s*$"


def writes(lines):
    for i, line in enumerate(lines):
        m = STORE.match(line)
        if not m:
            continue
        val = None
        for j in range(i - 1, max(-1, i - 13), -1):
            c = re.search(CONST.format(reg=m.group(2)), lines[j])
            if c:
                val = int(c.group(1), 0)
                break
        yield m.group(1), val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dis", nargs="+")
    ap.add_argument("--value", type=lambda s: int(s, 0))
    a = ap.parse_args()
    for f in a.dis:
        lines = open(f, encoding="utf-8").read().splitlines()
        for addr, val in writes(lines):
            if a.value is None or val == a.value:
                print(f"{f} {addr} M={'?' if val is None else hex(val)}")


if __name__ == "__main__":
    main()
