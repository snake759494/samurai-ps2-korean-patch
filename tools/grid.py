# 좌표 눈금을 그린 확대 크롭: grid.py src x0 y0 x1 y1 scale out
import sys
from PIL import Image, ImageDraw
src, x0, y0, x1, y1, sc, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1))
im = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
dr = ImageDraw.Draw(im)
for x in range(x0 - x0 % 16, x1, 16):
    if x < x0: continue
    X = (x - x0) * sc
    dr.line([(X, 0), (X, im.height)], fill=(0, 90, 160) if x % 64 else (200, 0, 0))
    dr.text((X + 1, 1), str(x), fill=(255, 255, 0))
for y in range(y0 - y0 % 16, y1, 16):
    if y < y0: continue
    Y = (y - y0) * sc
    dr.line([(0, Y), (im.width, Y)], fill=(0, 90, 160) if y % 64 else (200, 0, 0))
    dr.text((1, Y + 1), str(y), fill=(0, 255, 0))
im.save(out)
