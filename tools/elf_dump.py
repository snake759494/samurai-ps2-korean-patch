# ELF 문자열 후보 추출 → translation/elf_ja.tsv (off, cap, text)
import re, sys
e = open(sys.argv[1], 'rb').read()
out = open(sys.argv[2], 'w', encoding='utf-8')
pat = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e])+')
p = 0x100000
n = 0
while p < len(e):
    m = pat.match(e, p)
    if not m:
        p += 1; continue
    s = m.group()
    end = m.end()
    if end < len(e) and e[end] == 0 and (p == 0 or e[p - 1] == 0) and re.search(rb'[\x81-\x9f\xe0-\xef]', s):
        try:
            t = s.decode('cp932')
        except UnicodeDecodeError:
            p = end; continue
        if re.search('[぀-ヿ一-鿿！-～]', t) and len(s) >= 4:
            q = end
            while q < len(e) and e[q] == 0: q += 1
            out.write('%x\t%d\t%s\n' % (p, q - p - 1, t)); n += 1
    p = end
print(n)
