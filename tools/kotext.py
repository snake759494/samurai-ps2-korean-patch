# 한국어 번역문 → 게임 바이트열
import re
from fntbuild import SPACE_CODE

# ASCII/일반 기호 → 원본 전각 글리프
PUNCT = {
    '!': '！', '?': '？', ',': '，', '.': '．', '~': '～', '(': '（', ')': '）',
    ':': '：', ';': '；', '-': '－', '+': '＋', '/': '／', '%': '％', '&': '＆',
    '"': '”', "'": '’', '*': '＊', '=': '＝', '<': '＜', '>': '＞', '#': '＃',
    '‼': '√', '⁉': '〒',
}
for i in range(10):
    PUNCT[str(i)] = chr(0xFF10 + i)
for i in range(26):
    PUNCT[chr(65 + i)] = chr(0xFF21 + i)
    PUNCT[chr(97 + i)] = chr(0xFF41 + i)

HANGUL = re.compile('[가-힣]')
ESC = re.compile(r'(\\n|^@\d{3}|%s|%d)')   # 그대로 통과시키는 조각


def hangul_chars(texts):
    s = set()
    for t in texts:
        s.update(HANGUL.findall(t))
    return sorted(s)


def encode(text, charmap, valid=None):
    text = text.replace('!!', '‼').replace('!?', '⁉')
    out = bytearray()
    for part in ESC.split(text):
        if not part:
            continue
        if ESC.fullmatch(part):
            out += part.encode('ascii'); continue
        for ch in part:
            if ch in charmap:
                out += charmap[ch].to_bytes(2, 'big')
            elif ch == ' ':
                out += SPACE_CODE.to_bytes(2, 'big')
            else:
                g = PUNCT.get(ch, ch)
                b = g.encode('cp932')
                if len(b) != 2 or (valid is not None and int.from_bytes(b, 'big') not in valid):
                    raise ValueError('no glyph for %r in %r' % (ch, text))
                out += b
    return bytes(out)
