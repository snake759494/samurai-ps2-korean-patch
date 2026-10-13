# PIM 텍스처 컨테이너: 0x30 바이트 항목 나열. type 0x13=이미지, 0x14=CLUT
import struct
from PIL import Image


def entries(b):
    out = []
    p = 0
    while p + 0x30 <= len(b):
        t = b[p + 2]
        if t not in (0x13, 0x14) or b[p] != 0 or b[p + 1] not in (0, 0xfe):
            break
        w = struct.unpack_from('<12I', b, p)
        lw, lh = w[2] & 0xFFFF, w[2] >> 16
        ww, hh = w[4] & 0xFFFF, w[4] >> 16
        if t == 0x13:
            off, size = w[6], w[5]
        else:
            off, size = w[9], len(b) - w[9] if p + 0x30 >= len(b) or b[p + 0x32] not in (0x13, 0x14) else None
        out.append(dict(pos=p, type=t, lw=lw, lh=lh, w=ww, h=hh, size=size, off=off, words=w))
        p += 0x30
    return out


def dump(b):
    for e in entries(b):
        print({k: (hex(v) if isinstance(v, int) else '') for k, v in e.items() if k != 'raw'})


def clut_swz(i):
    return (i & 0xE7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)


def decode(b, img, clut, bpp, W, H):
    data = b[img['off']:img['off'] + img['size']]
    pal = []
    cd = b[clut['off']:clut['off'] + clut['size']]
    n = len(cd) // 4
    for i in range(n):
        j = clut_swz(i) if n == 256 else i
        r, g, bb, a = cd[4 * j:4 * j + 4]
        pal.append((r, g, bb, min(255, a * 2)))
    im = Image.new('RGBA', (W, H))
    px = []
    if bpp == 8:
        for v in data[:W * H]:
            px.append(pal[v])
    else:
        for v in data[:W * H // 2]:
            px.append(pal[v & 15]); px.append(pal[v >> 4])
    im.putdata(px)
    return im


def _swz8_index(x, y, w):
    block = (y & ~0xF) * w + (x & ~0xF) * 2
    swap = (((y + 2) >> 2) & 1) * 4
    posy = (((y & ~3) >> 1) + (y & 1)) & 7
    col = posy * w * 2 + ((x + swap) & 7) * 4
    byte = ((y >> 1) & 1) + ((x >> 2) & 2)
    return block + col + byte


def unswizzle8(buf, w, h):
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            out[y * w + x] = buf[_swz8_index(x, y, w)]
    return out


def swizzle8(lin, w, h):
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            out[_swz8_index(x, y, w)] = lin[y * w + x]
    return out


def palette(b, clut):
    cd = b[clut['off']:clut['off'] + 1024]
    pal = []
    for i in range(256):
        j = clut_swz(i)
        r, g, bb, a = cd[4 * j:4 * j + 4]
        pal.append((r, g, bb, min(255, a * 2)))
    return pal


def to_image(idx, pal, w, h):
    im = Image.new('RGBA', (w, h))
    im.putdata([pal[v] for v in idx])
    return im
