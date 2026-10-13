# font/Samurai.fnt + Samurai.pim
import struct
from PIL import Image
RANGES_OFF=0x34
def parse(f):
    nr=struct.unpack_from('<H',f,12)[0]
    rng=[struct.unpack_from('<HHI',f,RANGES_OFF+8*i) for i in range(nr)]
    cmap={}
    for lo,hi,off in rng:
        for k in range(hi-lo+1):
            p=struct.unpack_from('<I',f,off+4*k)[0]
            if p: cmap[lo+k]=struct.unpack_from('<HHBBBB',f,p)
    return rng,cmap
def layers(pim):
    L=[]
    for pg in range(2):
        raw=pim[0x60+pg*131072:0x60+(pg+1)*131072]
        for ly in range(2):
            px=bytearray()
            for b in raw:
                px.append((b>>(2*ly))&3); px.append((b>>(4+2*ly))&3)
            L.append(px)
    return L  # index pg*2+ly, 512x512 values 0..3
def glyph(L,rec):
    x,y,pg,ly,w,h=rec
    src=L[pg*2+ly]
    im=Image.new('L',(max(w,1),max(h,1)))
    im.putdata([src[(y+j)*512+x+i]*85 for j in range(h) for i in range(w)])
    return im
