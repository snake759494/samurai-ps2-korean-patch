# 8bpp PIM 그림 속 글자 교체. 명세: translation/img8_ko.tsv
#   pim  x0 y0 x1 y1  정렬(l/c)  글꼴  크기(px, 0=자동)  색(hex 또는 auto)  번역
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pim, gsmem
from images import FONTS


def load_specs(root):
    p = os.path.join(root, 'translation', 'img8_ko.tsv')
    specs = {}
    if not os.path.exists(p):
        return specs
    for line in open(p, encoding='utf-8'):
        line = line.rstrip('\r\n')
        if not line or line.startswith('#'):
            continue
        q = line.split('\t')
        specs.setdefault(int(q[0]), []).append(dict(box=tuple(map(int, q[1:5])), align=q[5], font=q[6],
                                                    size=int(q[7]), color=q[8], text=q[9]))
    return specs


def decode(b):
    E = pim.entries(b)
    x = [q for q in E if q['words'][5] > 0][0]
    w32, h32 = x['w'], x['h']
    W = 1 << x['lw']; H = w32 * h32 * 4 // W
    off, size = x['words'][6], x['words'][5]
    idx = gsmem.ct32_to_t8(b[off:off + size], w32, h32, W, H)
    pal = np.array(pim.palette(b, {'off': x['words'][9]}), np.int32)
    return idx, pal, (w32, h32, W, H, off, size)


def patch_one(b, items, root):
    idx, pal, (w32, h32, W, H, off, size) = decode(b)
    rgb = pal[idx][:, :, :3].astype(np.uint8)
    im = Image.fromarray(rgb, 'RGB')
    dr = ImageDraw.Draw(im)
    mask = np.zeros((H, W), bool)
    for it in items:
        x0, y0, x1, y1 = it['box']
        reg = idx[y0:y1, x0:x1]
        vals, cnt = np.unique(reg, return_counts=True)
        bgi = int(vals[cnt.argmax()])
        if it['color'] == 'auto':
            bgc = pal[bgi][:3]
            dist = np.abs(pal[vals][:, :3] - bgc).sum(1)
            ok = [(dd, v) for v, c, dd in zip(vals, cnt, dist) if c >= max(3, reg.size // 60)]
            fg = tuple(pal[max(ok)[1]][:3]) if ok else (255, 255, 255)
        else:
            fg = tuple(int(it['color'][k:k + 2], 16) for k in (0, 2, 4))
        bg = tuple(pal[bgi][:3])
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], fill=bg)
        mask[y0:y1, x0:x1] = True
        if it['text'] == '-':
            continue
        fp = os.path.join(root, FONTS[it['font']])
        if it['align'] == 'v':
            chars = [c for c in it['text'] if c != ' ']
            step = (y1 - y0) / len(chars)
            sz = it['size'] or int(min(x1 - x0, step) * 0.95)
            f = ImageFont.truetype(fp, sz)
            for k, c in enumerate(chars):
                dr.text(((x0 + x1) / 2, y0 + step * (k + 0.5)), c, font=f, fill=fg, anchor='mm')
            continue
        sz = it['size'] or int((y1 - y0) * 0.85)
        while True:
            f = ImageFont.truetype(fp, sz)
            if dr.textlength(it['text'], font=f) <= (x1 - x0) or sz <= 8:
                break
            sz -= 1
        cy = (y0 + y1) / 2
        if it['align'] == 'c':
            dr.text(((x0 + x1) / 2, cy), it['text'], font=f, fill=fg, anchor='mm')
        else:
            dr.text((x0, cy), it['text'], font=f, fill=fg, anchor='lm')
    # 바뀐 영역만 기존 팔레트로 양자화 (불투명 색만 후보)
    new = np.array(im).astype(np.int32)
    opaque = np.nonzero(pal[:, 3] >= 250)[0]
    cand = pal[opaque][:, :3]
    ys, xs = np.nonzero(mask)
    px = new[ys, xs]
    d = ((px[:, None, :] - cand[None, :, :]) ** 2).sum(2)
    idx2 = idx.copy()
    idx2[ys, xs] = opaque[d.argmin(1)]
    nb = bytearray(b)
    nb[off:off + size] = gsmem.t8_to_ct32(idx2, w32, h32, W, H)
    return bytes(nb), pal[idx2]


def patch_all(files, root, base=None):
    res = {}
    for i, items in load_specs(root).items():
        src = base.get(i, files[i]) if base else files[i]
        res[i], _ = patch_one(src, items, root)
    return res
