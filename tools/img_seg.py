# 4bpp 보기에서 글자 덩어리 분할 → 번호 붙은 미리보기 + bbox 목록
import sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

def seg(path, dil=(3, 6)):
    a = np.array(Image.open(path)) > 40
    m = ndimage.binary_dilation(a, structure=np.ones(dil))
    lab, n = ndimage.label(m)
    boxes = []
    for sl in ndimage.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if (y1 - y0) * (x1 - x0) < 60 or (y1 - y0) > 400 or (x1 - x0) > 600:
            continue
        sub = a[y0:y1, x0:x1]
        ys, xs = np.nonzero(sub)
        boxes.append((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1))
    boxes.sort(key=lambda b: (b[1] // 8, b[0]))
    return boxes

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    boxes = seg(src)
    im = Image.open(src).convert('RGB')
    dr = ImageDraw.Draw(im)
    for k, b in enumerate(boxes):
        dr.rectangle(b, outline=(255, 0, 0))
        dr.text((b[0], max(0, b[1] - 9)), str(k), fill=(0, 255, 0))
        print(k, *b)
    im.save(out)
