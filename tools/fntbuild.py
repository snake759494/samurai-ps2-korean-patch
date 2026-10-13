# 한글 폰트 생성: 원본 fnt/pim 의 기호·영숫자·가나는 유지, 한자 범위(0x889F~0x9872)를 한글로 교체
import struct
from PIL import Image, ImageDraw, ImageFont
import fnt

KANJI_LO, KANJI_HI = 0x889F, 0x9872
SPACE_CODE = 0x889F          # 좁은 공백 (한국어 띄어쓰기)
OVERRIDE = {0x8163: '…'}   # 원본 …는 세로 점(⋮)
# 저장 데이터의 기본 이름 「名無し侍」를 「이름없는무사」로 보이게 하는 예약 글리프
RESERVED = {0x96BC: '이름', 0x96B3: '없는', 0x82B5: '무', 0x8E98: '사'}
SPACE_W = 7                  # 공백 글리프 폭 (advance = w+1)
BAD_TRAIL = {0x40, 0x5C, 0x7B, 0x7D, 0x7F, 0x22, 0x23, 0x24}
CELL = 22
ROW = 23


def code_seq():
    c = SPACE_CODE + 1
    while c <= KANJI_HI:
        t = c & 0xFF
        if 0x40 <= t <= 0xFC and t not in BAD_TRAIL and c not in RESERVED:
            yield c
        c += 1


def render_hangul(ch, font, size_px):
    """22px 셀에 2bpp(0..3) 글리프. (w, rows) 반환"""
    S = 4
    n = max(2, len(ch) + 1)
    big = Image.new('L', (CELL * S * n, CELL * S), 0)
    dr = ImageDraw.Draw(big)
    dr.text((CELL * S * n // 2, CELL * S // 2), ch, font=font, fill=255, anchor='mm')
    sm = big.resize((CELL * n, CELL), Image.LANCZOS)
    bbox = sm.getbbox()
    if not bbox:
        return 0, []
    x0, x1 = bbox[0], bbox[2]
    w = x1 - x0
    px = sm.load()
    rows = []
    for y in range(CELL):
        r = []
        for x in range(x0, x1):
            v = px[x, y]
            r.append(0 if v < 40 else 1 if v < 110 else 2 if v < 185 else 3)
        rows.append(r)
    return w, rows


def build(orig_fnt, orig_pim, kochars, font_path, size_px=21, drop_kana=False):
    rng, cmap = fnt.parse(orig_fnt)
    L = fnt.layers(orig_pim)
    # 유지할 원본 글리프
    glyphs = {}   # code -> (w, rows, hbyte)
    for c, rec in cmap.items():
        if KANJI_LO <= c <= KANJI_HI:
            continue
        if drop_kana and (0x829F <= c <= 0x82F1 or 0x8340 <= c <= 0x8396):
            continue
        x, y, pg, ly, w, h = rec
        if pg > 1:   # 특수 항목은 그대로 둔다
            continue
        src = L[pg * 2 + ly]
        rows = [[src[(y + j) * 512 + x + i] for i in range(w)] for j in range(CELL)]
        glyphs[c] = (w, rows, h)
    glyphs[SPACE_CODE] = (SPACE_W, [[0] * SPACE_W for _ in range(CELL)], 0)
    font = ImageFont.truetype(font_path, size_px * 4)
    for c, ch in list(OVERRIDE.items()) + list(RESERVED.items()):          # 원본 글리프 대신 TTF로 다시 그릴 기호
        w, rows = render_hangul(ch, font, size_px)
        glyphs[c] = (w, rows, CELL)
    charmap = {}
    seq = code_seq()
    for ch in kochars:
        c = next(seq)
        w, rows = render_hangul(ch, font, size_px)
        glyphs[c] = (w, rows, CELL)
        charmap[ch] = c
    # 패킹
    layers = [bytearray(512 * 512) for _ in range(4)]
    recs = {}
    li, x, y = 0, 0, 0
    for c in sorted(glyphs):
        w, rows, h = glyphs[c]
        if x + w + 1 > 512:
            x = 0; y += ROW
            if y + CELL > 512:
                y = 0; li += 1
                if li >= 4:
                    raise RuntimeError('font texture full')
        for j in range(CELL):
            for i in range(w):
                layers[li][(y + j) * 512 + x + i] = rows[j][i]
        recs[c] = (x, y, li // 2, li % 2, w, h)
        x += w + 1
    # pim 픽셀 재조립
    pim = bytearray(orig_pim)
    for pg in range(2):
        a, b = layers[pg * 2], layers[pg * 2 + 1]
        out = bytearray(131072)
        for k in range(131072):
            p0 = a[2 * k] | (b[2 * k] << 2)
            p1 = a[2 * k + 1] | (b[2 * k + 1] << 2)
            out[k] = p0 | (p1 << 4)
        pim[0x60 + pg * 131072:0x60 + (pg + 1) * 131072] = out
    # fnt: 헤더·범위표·포인터표 크기 유지, 레코드 영역 재작성
    f = bytearray(orig_fnt)
    allptr = [struct.unpack_from('<I', orig_fnt, off) for lo, hi, off in rng]
    recstart = 0x4998
    special = orig_fnt[0x4848:recstart]
    body = bytearray()
    ptr = {}
    for c in sorted(recs):
        ptr[c] = recstart + len(body)
        body += struct.pack('<HHBBBB', *recs[c])
    for lo, hi, off in rng:
        for k in range(hi - lo + 1):
            struct.pack_into('<I', f, off + 4 * k, ptr.get(lo + k, 0))
    # 범위표 밖 보조 표(0x4848, 항목 = code u32, ptr u32): 한자이므로 빈 글리프로
    nextra = struct.unpack_from('<I', orig_fnt, 0x14)[0]
    for k in range(nextra):
        struct.pack_into('<I', f, 0x4848 + 8 * k + 4, ptr[SPACE_CODE])
    f = f[:recstart] + body
    return bytes(f), bytes(pim), charmap, (li, y)

# 번역문 외에 폰트에 꼭 넣을 글자(이름 입력 표 등)
EXTRA_TEXT = []
