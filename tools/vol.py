# VOLUME.DAT (FADEBABE) 아카이브: 헤더 0x14, 항목 24B BE (hash, off, size, 0, end, namelen), 데이터 기준 0x17800
import struct
BASE=0x17800
def load(path):
    d=open(path,'rb').read()
    n=struct.unpack('>I',d[8:12])[0]
    ents=[list(struct.unpack('>6I',d[0x14+i*24:0x14+i*24+24])) for i in range(n)]
    files=[d[BASE+e[1]:BASE+e[1]+e[2]] for e in ents]
    return d,ents,files
def patch(d,ents,newfiles):
    """newfiles: {index: bytes}. 원래 슬롯(다음 파일 전까지)에 들어가면 제자리, 아니면 끝에 추가."""
    d=bytearray(d); orig_len=len(d); grew=False
    starts=sorted(e[1] for e in ents)
    for i,f in sorted(newfiles.items()):
        e=ents[i]
        nxt=[s for s in starts if s>e[1]]
        cap=(nxt[0] if nxt else len(d)-BASE)-e[1]
        if len(f)<=cap:
            off=e[1]; d[BASE+off:BASE+off+cap]=f+b'\0'*(cap-len(f))
        else:
            while len(d)%2048: d.append(0)
            off=len(d)-BASE; d+=f; grew=True
        e[1]=off; e[2]=len(f); e[4]=off+len(f)
        d[0x14+i*24:0x14+i*24+24]=struct.pack('>6I',*e)
    if grew:
        # 원본과 같은 '2048 나머지'를 유지 (2048 배수 크기면 게임이 부팅 중 멈춤)
        rem = orig_len % 2048
        while len(d) % 2048 != rem:
            d.append(0)
        # 헤더 0x10: 데이터 영역 크기 (BASE + 값 = 2048 정렬된 파일 끝)
        struct.pack_into('>I', d, 0x10, (len(d) + 2047) // 2048 * 2048 - BASE)
    return bytes(d)
