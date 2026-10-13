# 이름이 밝혀진 PIM 들을 4bpp 보기로 렌더링 → work/survey/
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
import vol, pim, gsmem

NAMES = {}
for line in open(sys.argv[1], encoding='utf-8'):
    p = line.split()
    if len(p) >= 2 and p[1].endswith('.pim'):
        NAMES[int(p[0])] = p[1]
d, ents, files = vol.load('VOLUME.DAT')
os.makedirs('survey', exist_ok=True)
for i, n in sorted(NAMES.items()):
    if 'vsk_face' in n or n.startswith('map/') or n.startswith('chara/') or 'weapons' in n:
        continue
    b = files[i]
    E = pim.entries(b)
    imgs = [e for e in E if e['words'][5] > 0]
    if not imgs:
        print(i, n, 'no image entry'); continue
    e = imgs[0]
    w32, h32 = e['w'], e['h']
    W = 1 << e['lw']
    data = b[e['words'][6]:e['words'][6] + e['words'][5]]
    if len(data) < w32 * h32 * 4:
        print(i, n, 'short', w32, h32, len(data)); continue
    mem = gsmem.mem_from_ct32(data, w32, h32)
    bw = max(2, W // 64)
    H4 = len(mem) * 2 // (bw * 64)
    v = gsmem.read4(mem, bw * 64, H4, bw)
    out = n.replace('/', '_')
    Image.fromarray((v * 17).astype(np.uint8)).save('survey/%03d_%s.png' % (i, out))
    print(i, n, w32, h32, 'T4', bw * 64, H4, [hex(x['type']) for x in E])
