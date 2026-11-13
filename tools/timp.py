"""TIMP archives (.TMP): a list of BPE-compressed entries, usually TIMs. Verified against SLPS_031.33.

Layout: b"TIMP", then per entry (offset, unc_size, comp_size) as u32 LE, offset from file start; offset -1 ends the
list. Loader 0x800143C4 / 0x800144F8, decompressor 0x800141AC: Philip Gage's byte pair encoding, blocks until
comp_size bytes are read. Block: pair table (count byte; >=0x80 skips count-127 codes, else count+1 entries of
left[, right] where left == code means a literal), u16 BE size, then size bytes expanded through the table.

usage: timp.py list FILE.. | timp.py x FILE OUTDIR (writes NN.bin per entry)
"""
import struct
import sys
from pathlib import Path

MAGIC = b"TIMP"


def entries(data):
    """[(offset, unc_size, comp_size)]"""
    assert data[:4] == MAGIC, "not a TIMP file"
    out, p = [], 4
    while True:
        off = struct.unpack_from("<i", data, p)[0]
        if off == -1:
            return out
        out.append(struct.unpack_from("<III", data, p))
        p += 12


def bpe_decode(src, comp_size):
    out = bytearray()
    p = 0
    while p < comp_size:
        left = list(range(256))
        right = [0] * 256
        c = 0
        while True:
            count = src[p]; p += 1
            if count > 127:
                c += count - 127
                count = 0  # a skip is still followed by one entry
            if c == 256:
                break
            for _ in range(count + 1):
                left[c] = src[p]; p += 1
                if left[c] != c:
                    right[c] = src[p]; p += 1
                c += 1
            if c == 256:
                break
        size = src[p] << 8 | src[p + 1]; p += 2
        for b in src[p:p + size]:
            stack = [b]
            while stack:
                b = stack.pop()
                if left[b] == b:
                    out.append(b)
                else:
                    stack.append(right[b])
                    stack.append(left[b])
        p += size
    return bytes(out)


def unpack(data):
    """[bytes] decompressed entries."""
    res = []
    for off, unc, comp in entries(data):
        d = bpe_decode(data[off:off + comp], comp)
        assert len(d) == unc, f"entry at {off:#x}: {len(d)} bytes, header says {unc}"
        res.append(d)
    return res


def bpe_store(data):
    """Encode with no pairs (literal blocks): exact and simple, but no smaller than the input."""
    out = bytearray()
    for i in range(0, len(data), 0xFFFF):
        blk = data[i:i + 0xFFFF]
        out += b"\xff\x80\xfe" + struct.pack(">H", len(blk)) + blk  # skip to 128, 128 literal, skip to 256
    return bytes(out)


def pack(blobs, comp=None):
    """Build a TIMP file. comp[i] (optional) is entry i's compressed bytes, kept as-is (identity build)."""
    comp = list(comp) if comp else [bpe_store(b) for b in blobs]
    off = 4 + 12 * len(blobs) + 4
    head, body = bytearray(MAGIC), bytearray()
    for b, c in zip(blobs, comp):
        head += struct.pack("<III", off + len(body), len(b), len(c))
        body += c
    head += struct.pack("<i", -1)
    return bytes(head + body)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["-h"]
    if cmd == "list":
        for f in args:
            d = Path(f).read_bytes()
            for i, (off, unc, comp) in enumerate(entries(d)):
                print(f"{f}\t{i}\t{off:#x}\t{unc}\t{comp}")
    elif cmd == "x":
        out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
        for i, b in enumerate(unpack(Path(args[0]).read_bytes())):
            (out / f"{i:02d}.bin").write_bytes(b)
    else:
        sys.exit(__doc__)
