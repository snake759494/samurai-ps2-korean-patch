# 평문 스크립트(SJIS) 문자열 추출/치환
import re
SJ = re.compile(rb'[\x81-\x9f\xe0-\xef]')
SR = re.compile(rb'"((?:[\x81-\x9f\xe0-\xef][\x40-\xfc]|[^"\x81-\x9f\xe0-\xef])*)"')


def is_script(f):
    if f[:1] not in b'# $\t\r\n' or b'$' not in f[:4000]:
        return False
    t = f.rstrip(b'\x00')
    if sum(1 for b in t if b < 9 or 13 < b < 32):
        return False
    try:
        for m in SR.finditer(f):
            if SJ.search(m.group(1)):
                m.group(1).decode('cp932')
    except UnicodeDecodeError:
        return False
    return True


def strings(f):
    for m in SR.finditer(f):
        s = m.group(1)
        if SJ.search(s):
            yield m.start(1), m.end(1), s.decode('cp932')


def replace(f, tr):
    """tr: ja -> 바이트열"""
    out = bytearray(); p = 0
    for a, b, j in strings(f):
        out += f[p:a]; out += tr[j]; p = b
    out += f[p:]
    return bytes(out)
