# raw MODE2/2352 CD 이미지 ISO9660 읽기/쓰기 도구
import struct, sys
SS=2352
class CD:
    def __init__(s,path,mode='rb'):
        s.f=open(path,mode)
    def read(s,lba,n=1):
        out=bytearray()
        for i in range(n):
            s.f.seek((lba+i)*SS+24); out+=s.f.read(2048)
        return bytes(out)
    def readfile(s,lba,size):
        return s.read(lba,(size+2047)//2048)[:size]
    def walk(s):
        pvd=s.read(16)
        root=pvd[156:156+34]
        res=[]
        def rec(lba,size,path):
            data=s.read(lba,(size+2047)//2048)
            p=0
            while p<len(data):
                l=data[p]
                if l==0:
                    p=(p//2048+1)*2048; continue
                e=data[p:p+l]
                elba=struct.unpack_from('<I',e,2)[0]; esz=struct.unpack_from('<I',e,10)[0]
                fl=e[25]; nl=e[32]; name=e[33:33+nl]
                if name not in (b'\0',b'\1'):
                    nm=name.decode('latin1').split(';')[0]
                    if fl&2: rec(elba,esz,path+nm+'/')
                    else: res.append((path+nm,elba,esz,lba*2048+p))  # p: dir record offset (logical)
                p+=l
        rec(struct.unpack_from('<I',root,2)[0],struct.unpack_from('<I',root,10)[0],'/')
        return res
if __name__=='__main__':
    c=CD(sys.argv[1])
    for n,l,sz,_ in c.walk(): print(f'{l:8d} {sz:10d} {n}')
