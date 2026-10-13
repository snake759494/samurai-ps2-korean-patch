# 전체 빌드: python build.py [--test]
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
import vol, fnt, fntbuild, kotext, scr, isobuild

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, 'Samurai (Japan, Asia).bin')
OUT = os.path.join(ROOT, 'Samurai (Korean).iso')
WORK = os.path.join(ROOT, 'work')
TR = os.path.join(ROOT, 'translation')
FONT = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')
FNT_I, PIM_I = 470, 471


def load_script_tr(test=False):
    G = json.load(open(os.path.join(TR, 'script_ja.json'), encoding='utf-8'))
    ja = [s for g in G for s in g['strings']]
    if test:
        return {j: ('@' + j[1:4] if re.match(r'@\d{3}', j) else '') + '테스트 %d 가나다 한글 출력\\n둘째 줄입니다!' % k for k, j in enumerate(ja)}
    ko = {}
    for fn in sorted(os.listdir(TR)):
        if fn.startswith('script_ko') and fn.endswith('.tsv'):
            for line in open(os.path.join(TR, fn), encoding='utf-8'):
                line = line.rstrip('\r\n')
                if not line or line.startswith('#'):
                    continue
                k, _, t = line.partition('\t')
                if t:
                    ko[ja[int(k)]] = t
    return ko


def ensure_extracted():
    os.makedirs(WORK, exist_ok=True)
    need = [n for n in ('VOLUME.DAT', 'SLPS_201.78') if not os.path.exists(os.path.join(WORK, n))]
    if need:
        from cdimg import CD
        c = CD(BIN)
        for n, l, sz, _ in c.walk():
            if n[1:] in need:
                open(os.path.join(WORK, n[1:]), 'wb').write(c.readfile(l, sz))


def main():
    test = '--test' in sys.argv
    ensure_extracted()
    vd, ents, files = vol.load(os.path.join(WORK, 'VOLUME.DAT'))
    elf = open(os.path.join(WORK, 'SLPS_201.78'), 'rb').read()
    tr = load_script_tr(test)
    import elfstr
    elf_tr = {} if test else elfstr.load(TR)
    texts = list(tr.values()) + (elfstr.texts(elf_tr) if elf_tr else []) + fntbuild.EXTRA_TEXT
    name_syl = elfstr.name_syllables(texts)
    chars = kotext.hangul_chars(texts + [''.join(name_syl)])
    print('hangul syllables', len(chars))
    f, p, cmap, used = fntbuild.build(files[FNT_I], files[PIM_I], chars, FONT)
    print('font texture used (layer,y)', used)
    valid = set(fnt.parse(f)[1].keys())
    new = {} if '--no-font' in sys.argv else {FNT_I: f, PIM_I: p}
    enc = {}
    missing = 0
    for j in set(s for i, fl in enumerate(files) if scr.is_script(fl) for _, _, s in scr.strings(fl)):
        if j in tr and tr[j].strip():
            enc[j] = kotext.encode(tr[j], cmap, valid)
        else:
            missing += 1
            enc[j] = j.encode('cp932')
    print('script strings untranslated', missing)
    for i, fl in enumerate(files):
        if scr.is_script(fl) and '--no-script' not in sys.argv:
            nf = scr.replace(fl, enc)
            if nf != fl:
                mode = os.environ.get('SCRIPT_FIT')
                fits = len(nf) <= ((len(fl) + 2047) // 2048) * 2048
                if mode == 'fit' and not fits: continue
                if mode == 'grow' and fits: continue
                new[i] = nf
    if elf_tr and '--no-elf' not in sys.argv:
        elf = elfstr.patch(elf, elf_tr, cmap, valid, name_syl)
    for k, v in images_patch(files).items():
        new[k] = v
    vd2 = vol.patch(vd, ents, new)
    print('VOLUME.DAT', len(vd), '->', len(vd2))
    n = isobuild.build(BIN, OUT, {'/VOLUME.DAT': vd2, '/SLPS_201.78': elf})
    print('ISO sectors', n, OUT)


def images_patch(files):
    try:
        import images
    except ImportError:
        return {}
    return images.patch_all(files, ROOT)


if __name__ == '__main__':
    main()
