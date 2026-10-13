# 빌드된 폰트로 번역문 렌더링 미리보기 (게임 렌더러 규칙: advance = w+1, 0x8140 = 22px, 줄 간격 24px)
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
import vol, fnt, fntbuild, kotext, build, elfstr

def main(ids, out):
    vd, ents, files = vol.load(os.path.join(build.WORK, 'VOLUME.DAT'))
    tr = build.load_script_tr()
    ed = elfstr.load(build.TR)
    texts = list(tr.values()) + elfstr.texts(ed)
    chars = kotext.hangul_chars(texts + [''.join(elfstr.name_syllables(texts))])
    f, p, cmap, _ = fntbuild.build(files[build.FNT_I], files[build.PIM_I], chars, build.FONT)
    rng, recs = fnt.parse(f); L = fnt.layers(p)
    import json
    G = json.load(open(os.path.join(build.TR, 'script_ja.json'), encoding='utf-8'))
    ja = [s for g in G for s in g['strings']]
    blocks = []
    for i in ids:
        b = kotext.encode(tr[ja[i]], cmap)
        b = re.sub(rb'^@\d{3}', b'', b)
        lines = b.split(b'\\n')
        img = Image.new('L', (300, 24 * len(lines) + 8), 40)
        for li, ln in enumerate(lines):
            x = 6; k = 0
            while k < len(ln):
                c = ln[k] << 8 | ln[k + 1]; k += 2
                if c == 0x8140: x += 22; continue
                r = recs[c]
                img.paste(fnt.glyph(L, r), (x, 4 + li * 24)); x += r[4] + 1
        blocks.append(img)
    H = sum(b.height + 4 for b in blocks)
    sheet = Image.new('L', (300, H), 0); y = 0
    for b in blocks:
        sheet.paste(b, (0, y)); y += b.height + 4
    sheet = sheet.resize((600, H * 2), Image.NEAREST)
    sheet.save(out)

if __name__ == '__main__':
    main([int(x) for x in sys.argv[1].split(',')], sys.argv[2])
