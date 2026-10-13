# PIM 텍스처 안의 4bpp 글자 영역을 한글로 다시 그림
# 명세: translation/img_ko.tsv  —  pim번호  x0  y0  x1  y1  모드(h/v/hl)  글꼴  번역
#   좌표는 4bpp 보기(img_survey) 기준, 모드 h=가로 가운데, hl=가로 왼쪽, v=세로쓰기
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pim, gsmem

FONTS = {'serif': 'SeoulHangangB.ttf', 'serifm': 'SeoulHangangM.ttf', 'sans': 'NanumSquareNeo-cBd.ttf',
         'sansh': 'NanumSquareNeo-dEb.ttf'}


def load_specs(root):
    specs = {}
    for line in open(os.path.join(root, 'translation', 'img_ko.tsv'), encoding='utf-8'):
        line = line.rstrip('\r\n')
        if not line or line.startswith('#'):
            continue
        p = line.split('\t')
        i, x0, y0, x1, y1 = map(int, p[:5])
        specs.setdefault(i, []).append(dict(box=(x0, y0, x1, y1), mode=p[5], font=p[6], text=p[7]))
    return specs


def render(text, w, h, mode, font_path, maxv):
    S = 4
    W, H = w * S, h * S
    big = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(big)
    if mode == 'h2':
        top, bot = text.split('/')
        f1 = ImageFont.truetype(font_path, int(H * 0.62)); f2 = ImageFont.truetype(font_path, int(H * 0.36))
        dr.text((W / 2, H * 0.32), top, font=f1, fill=255, anchor='mm')
        dr.text((W / 2, H * 0.82), bot, font=f2, fill=255, anchor='mm')
    elif mode == 'v':
        chars = [c for c in text]
        size = min(W, int(H / max(1, len(chars)) * 1.05))
        f = ImageFont.truetype(font_path, max(8, size))
        step = H / max(1, len(chars))
        for k, c in enumerate(chars):
            dr.text((W / 2, step * (k + 0.5)), c, font=f, fill=255, anchor='mm')
    else:
        size = int(H * 0.92)
        while True:
            f = ImageFont.truetype(font_path, size)
            tw = dr.textlength(text, font=f)
            if tw <= W * 0.98 or size < 8:
                break
            size -= 2
        x = W / 2 if mode == 'h' else 0
        dr.text((x, H / 2), text, font=f, fill=255, anchor='mm' if mode == 'h' else 'lm')
    sm = np.array(big.resize((w, h), Image.LANCZOS)).astype(float) / 255
    return np.clip(np.round(sm * maxv), 0, maxv).astype(np.uint8)


def learn_order(reg, bg):
    """원본 글자 픽셀에서 '가장자리→중심' 인덱스 순서를 추정"""
    from scipy import ndimage
    m = reg != bg
    if m.sum() < 8:
        return None
    nb = ndimage.uniform_filter(m.astype(float), 3) * 9 - 1
    order = []
    for k in np.unique(reg[m]):
        sel = reg == k
        if sel.sum() >= max(3, m.sum() // 200):
            order.append((nb[sel].mean(), int(k)))
    order.sort()
    return [k for _, k in order] or None


def apply_order(cov, order, bg, maxv):
    """cov: 0..maxv 단계 → 학습된 인덱스"""
    c = cov.astype(float) / max(1, maxv)
    out = np.full(cov.shape, bg, np.uint8)
    n = len(order)
    lv = np.clip((c - 0.2) / 0.8 * n, 0, n - 1).astype(int)
    out[c >= 0.2] = np.array(order, np.uint8)[lv[c >= 0.2]]
    return out


def write4(mem, v, bw):
    h, w = v.shape
    a = gsmem.addr4(w, h, bw)
    flat_a = a.ravel(); flat_v = v.ravel().astype(np.uint8)
    byte = flat_a >> 1
    lo = (flat_a & 1) == 0
    m = mem.copy()
    m[byte[lo]] = (m[byte[lo]] & 0xF0) | flat_v[lo]
    m[byte[~lo]] = (m[byte[~lo]] & 0x0F) | (flat_v[~lo] << 4)
    return m


def patch_one(b, items, root):
    E = pim.entries(b)
    e = [x for x in E if x['words'][5] > 0][0]
    w32, h32 = e['w'], e['h']
    off, size = e['words'][6], e['words'][5]
    mem = gsmem.mem_from_ct32(b[off:off + size], w32, h32)
    bw = max(2, (1 << e['lw']) // 64)
    H4 = len(mem) * 2 // (bw * 64)
    v = gsmem.read4(mem, bw * 64, H4, bw).astype(np.uint8)
    for it in items:
        x0, y0, x1, y1 = it['box']
        reg = v[y0:y1, x0:x1]
        orig = reg.copy()
        maxv = int(reg.max()) or 15
        vals, cnt = np.unique(reg, return_counts=True)
        bg = int(vals[cnt.argmax()]) if it.get('bg', True) else 0
        reg[:] = bg
        if it['text'] == '-':
            continue
        mode = it['mode']; fp = os.path.join(root, FONTS[it['font']])
        asc = mode.endswith('!asc')
        if asc:
            mode = mode[:-4]
            it['order'] = [k for k in range(16) if k != bg and k > bg]
        if mode.startswith('vc@'):
            cx, pitch = map(float, mode[3:].split(':'))
            r = vcols(it['text'], x0, y0, x1, y1, cx, pitch, fp, maxv)
        elif '@' in mode:
            m, rest = mode.split('@'); W, o = map(int, rest.split(':'))
            full = render(it['text'], W, y1 - y0, m, fp, maxv)
            r = full[:, o:o + (x1 - x0)]
        else:
            r = render(it['text'], x1 - x0, y1 - y0, mode, fp, maxv)
        order = it.get('order') or learn_order(orig, bg)
        if order:
            reg[:] = np.where(r > 0, apply_order(r, order, bg, maxv), bg)
        else:
            reg[:] = np.maximum(r, bg) if bg < maxv else r
    mem2 = write4(mem, v, bw)
    a = gsmem.addr32(w32, h32, w32 // 64)
    out = np.zeros((h32, w32, 4), np.uint8)
    for k in range(4):
        out[:, :, k] = mem2[a + k]
    nb = bytearray(b)
    nb[off:off + size] = out.tobytes()
    return bytes(nb), v


def patch_all(files, root):
    if not os.path.exists(os.path.join(root, 'translation', 'img_ko.tsv')):
        return {}
    res = {}
    for i, items in load_specs(root).items():
        res[i], _ = patch_one(files[i], items, root)
    return res


def vcols(text, x0, y0, x1, y1, cx, pitch, font_path, maxv, size=21, step=23):
    """세로쓰기 여러 열: 오른쪽 열 중심 cx 부터 왼쪽으로 pitch 간격"""
    S = 4
    w, h = x1 - x0, y1 - y0
    big = Image.new('L', (w * S, h * S), 0)
    dr = ImageDraw.Draw(big)
    f = ImageFont.truetype(font_path, size * S)
    ROT = set('「」『』…-~()（）ー')
    for j, col in enumerate(text.split('|')):
        units = [0.5 if c == ' ' else 1.0 for c in col]
        st = min(step, h / max(1.0, sum(units)))
        x = (cx - pitch * j - x0) * S
        yy = 0.0
        for c, u in zip(col, units):
            ymid = (yy + u * st / 2) * S
            yy += u * st
            if c == ' ':
                continue
            if c in ROT:
                t = Image.new('L', (size * S * 2, size * S * 2), 0)
                ImageDraw.Draw(t).text((size * S, size * S), c, font=f, fill=255, anchor='mm')
                t = t.rotate(-90)
                big.paste(255, (int(x - size * S), int(ymid - size * S)), t)
            else:
                dr.text((x, ymid), c, font=f, fill=255, anchor='mm')
    sm = np.array(big.resize((w, h), Image.LANCZOS)).astype(float) / 255
    return np.clip(np.round(sm * maxv), 0, maxv).astype(np.uint8)


def _patch_all_with8(files, root):
    res = _patch_all4(files, root)
    import images8
    res.update(images8.patch_all(files, root, base=res))
    print('images patched', len(res))
    return res


_patch_all4 = patch_all
patch_all = _patch_all_with8
