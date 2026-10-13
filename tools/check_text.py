# 번역 검사: 누락, 줄 수, 줄 폭(원문 대비), 금지 문자
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import build

NL = chr(92) + 'n'
KO_ADV = 21          # 한글 advance(px) 추정
LIMIT = 280          # 대사 한 줄 최대 폭(px)


def width(line):
    w = 0
    for ch in re.sub(r'^@\d{3}', '', line):
        if '가' <= ch <= '힣': w += KO_ADV
        elif ch == ' ': w += 8
        elif ch == '　': w += 22
        else: w += 15
    return w


def main():
    G = json.load(open(os.path.join(build.TR, 'script_ja.json'), encoding='utf-8'))
    ja = [s for g in G for s in g['strings']]
    tr = build.load_script_tr()
    miss = [i for i, j in enumerate(ja) if j not in tr]
    print('missing', len(miss), miss[:20])
    bad = 0
    for i, j in enumerate(ja):
        k = tr.get(j)
        if k is None: continue
        if re.search(r'[぀-ヿ一-鿿]', k):
            print('JP left', i, k); bad += 1
        if j.startswith('@') and not k.startswith(j[:4]):
            print('voice tag', i, k); bad += 1
        lines = k.split(NL)
        if len(lines) > max(4, j.count(NL) + 1):
            print('lines', i, k); bad += 1
        jw = max(width(l) for l in j.split(NL))
        for l in lines:
            if width(l) > max(LIMIT, jw + 10):
                print('wide', i, width(l), l); bad += 1
    print('problems', bad)


if __name__ == '__main__':
    main()
