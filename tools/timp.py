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


def bpe_encode(data, block=5000, max_stack=64, threshold=3):
    """Gage BPE in the game's format, so an edited entry stays about as small as the original. Limits stay inside
    what the disc's own streams already make the game's decoder do (docs/re/disc.md: decoder stack up to 78 entries,
    15,623 bytes out of one block): input blocks of `block` bytes, pair nesting kept to `max_stack` stack entries."""
    import numpy as np
    out, i = bytearray(), 0
    while i < len(data):
        seen, j = set(), i  # Gage's block: stop at `block` bytes or 200 distinct ones, leaving codes for pairs
        while j < len(data) and j - i < block and (data[j] in seen or len(seen) < 200):
            seen.add(data[j])
            j += 1
        buf, i = data[i:j], j
        left, right, stack = list(range(256)), [0] * 256, [1] * 256
        free = [c for c in range(256) if c not in set(buf)]
        while free and len(buf) > 1:
            a = np.frombuffer(buf, np.uint8).astype(np.int32)
            cnt = np.bincount(a[:-1] * 256 + a[1:], minlength=65536)
            while True:
                p = int(cnt.argmax())
                x, y = divmod(p, 256)
                s = max(2, 1 + stack[x], stack[y])
                if cnt[p] < threshold or s <= max_stack:
                    break
                cnt[p] = 0
            if cnt[p] < threshold:
                break
            c = free.pop()
            left[c], right[c], stack[c] = x, y, s
            buf = buf.replace(bytes((x, y)), bytes((c,)))
        c = 0
        while c < 256:
            if left[c] == c:  # run of literals: a skip byte, then one entry always follows unless the table ended
                n = 1
                while n < 128 and c + n < 256 and left[c + n] == c + n:
                    n += 1
                out.append(n + 127)
                c += n
                if c == 256:
                    break
                ents = [c]
            else:
                n = 1
                while n < 128 and c + n < 256 and left[c + n] != c + n:
                    n += 1
                out.append(n - 1)
                ents = range(c, c + n)
            for e in ents:
                out.append(left[e])
                if left[e] != e:
                    out.append(right[e])
            c = ents[-1] + 1
        out += struct.pack(">H", len(buf)) + buf
    return bytes(out)


def bpe_best(data):
    """The smallest of bpe_encode at a few block sizes, all within the 15,623-byte block the disc's own streams already
    make the decoder take (docs/re/disc.md): an archive may not grow, as files keep their size (disc.write_file)."""
    return min((bpe_encode(data, block=k) for k in (5000, 8000, 15000)), key=len)


def align_of(data):
    """4 when the archive shows word padding (a gap before an entry or after the last one: 56 of 196 disc archives),
    else 1. An archive aligned by chance with no gap packs the same either way, so it gets the tighter 1."""
    es = entries(data)
    pos, gap = 4 + 12 * len(es) + 4, False
    for o, _, c in es:
        gap |= o != pos
        pos = o + c
    return 4 if (gap or pos != len(data)) and all(o % 4 == 0 for o, _, _ in es) else 1


def pack(blobs, comp=None, align=1):
    """Build a TIMP file. comp[i] (optional) is entry i's compressed bytes, kept as-is (identity build)."""
    comp = list(comp) if comp else [bpe_store(b) for b in blobs]
    assert len(comp) == len(blobs), f"{len(blobs)} blobs, {len(comp)} compressed streams"
    off = 4 + 12 * len(blobs) + 4
    head, body = bytearray(MAGIC), bytearray()
    for b, c in zip(blobs, comp):
        body += bytes(-(off + len(body)) % align)
        head += struct.pack("<III", off + len(body), len(b), len(c))
        body += c
    head += struct.pack("<i", -1)
    out = head + body
    return bytes(out + bytes(-len(out) % align))


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
