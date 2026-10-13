# ELF 시스템 문자열 제자리 교체 + 이름 입력 격자 한글화
import os
import kotext

GRIDS = [(0x10ba80, 255), (0x10bb80, 255), (0x10bd80, 1535)]   # 히라가나, 가타카나, 한자 표
NAME_SYL = ('가각간갈감강개거건검겸경계고곤공곽관광구국군권귀규균근금기길김나남내노다단달담당대덕도동두득라란람랑래려련렬령로록료룡류륜률리린림마만명모목몽무문미민박방배백범법변병보복봉부분비빈사산상서석선설섬성세소손솔송수숙순술숭슬승시식신실심아안암야양어언엄여연열염영예오옥온완왕요용우욱운웅원월위유윤율은을음의이익인일임자장재전정제조종주준중지진찬창채천철청초총최춘충치친칠탁태택토판팔평표풍하학한함해행향허혁현형혜호홍화환황회효후훈휘흥희'
            '쓰코키치타테토카케쿠소하히후헤모요로루레리나니누네노마미무메야유와')
JP = __import__('re').compile('[぀-ヿ一-鿿]')


def load(trdir):
    tr = {}
    for line in open(os.path.join(trdir, 'elf_ko.tsv'), encoding='utf-8'):
        line = line.rstrip('\r\n')
        if not line or line.startswith('#'):
            continue
        k, _, t = line.partition('\t')
        tr[int(k, 16)] = t
    caps = {}
    for line in open(os.path.join(trdir, 'elf_ja.tsv'), encoding='utf-8'):
        k, c, t = line.rstrip('\n').split('\t', 2)
        caps[int(k, 16)] = (int(c), t)
    return {'tr': tr, 'caps': caps}


def name_syllables(other_texts):
    s = set(NAME_SYL)
    for t in other_texts:
        s.update(kotext.HANGUL.findall(t))
    return sorted(s)


def texts(d):
    return list(d['tr'].values())


def patch(elf, d, cmap, valid, name_syl):
    e = bytearray(elf)
    base = 0  # 파일 오프셋 그대로
    over = []
    for off, ko in d['tr'].items():
        cap, ja = d['caps'][off]
        b = kotext.encode(ko, cmap, valid)
        if len(b) > cap:
            over.append((hex(off), len(b), cap, ko)); continue
        e[off:off + cap + 1] = b + b'\0' * (cap + 1 - len(b))
    if over:
        for o in over: print('ELF overflow', o)
        raise SystemExit(1)
    # 이름 입력 격자
    it = iter(name_syl)
    for off, cap in GRIDS:
        raw = bytes(e[off:off + cap + 1]).split(b'\0')[0]
        out = bytearray()
        for i in range(0, len(raw), 2):
            pair = raw[i:i + 2]
            if pair == b'\x81\x40':
                out += pair; continue
            ch = next(it, None)
            out += cmap[ch].to_bytes(2, 'big') if ch else b'\x81\x40'
        e[off:off + len(out)] = out
    return bytes(e)
