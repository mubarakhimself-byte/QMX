"""Rough text extraction from a PDF using only the standard library (FlateDecode streams)."""
import re
import sys
import zlib

BS = b"\x5c"  # backslash

def unescape(b):
    b = b.replace(BS + b"(", b"(").replace(BS + b")", b")")
    b = b.replace(BS + BS, BS)
    return b

data = open(sys.argv[1], "rb").read()
out = []
str_re = re.compile(rb"\((?:[^()\x5c]|\x5c.)*\)", re.S)
for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
    s = m.group(1)
    try:
        d = zlib.decompress(s)
    except Exception:
        continue
    parts = []
    # walk tokens: strings, numbers inside TJ arrays, and line operators
    tok_re = re.compile(rb"\((?:[^()\x5c]|\x5c.)*\)|-?\d+\.?\d*|T\*|Td|TD|ET|TJ|Tj|'", re.S)
    for t in tok_re.finditer(d):
        g = t.group(0)
        if g.startswith(b"("):
            parts.append(unescape(g[1:-1]))
        elif g in (b"ET", b"T*", b"'"):
            parts.append(b"\n")
        elif g in (b"Td", b"TD"):
            parts.append(b" ")
        elif g in (b"TJ", b"Tj"):
            pass
        else:
            try:
                if float(g) < -200:
                    parts.append(b" ")
            except ValueError:
                pass
    txt = b"".join(parts)
    if txt.strip():
        out.append(txt.decode("latin-1"))
sys.stdout.buffer.write("\n=====\n".join(out).encode("utf-8", "replace"))
