# 원본 BIN(MODE2/2352) → 2048 섹터 ISO 로 변환하면서 파일 교체.
# VOLUME.DAT 는 디스크 마지막 파일이므로 커져도 뒤로 늘리면 된다. SLPS 는 제자리(크기 동일).
import struct, sys
from cdimg import CD


def both32(v):
    return struct.pack('<I', v) + struct.pack('>I', v)


def build(bin_path, out_path, replace):
    """replace: {'/VOLUME.DAT': bytes, '/SLPS_201.78': bytes}"""
    cd = CD(bin_path)
    total = cd.f.seek(0, 2) // 2352
    ents = {n: (lba, sz, rec) for n, lba, sz, rec in cd.walk()}
    last = max(l + (s + 2047) // 2048 for l, s, _ in ents.values())
    with open(out_path, 'wb') as o:
        for i in range(0, total, 4096):
            o.write(cd.read(i, min(4096, total - i)))
        newtotal = total
        for name, data in replace.items():
            lba, sz, rec = ents[name]
            nsec = (len(data) + 2047) // 2048
            if lba + (sz + 2047) // 2048 != last and nsec > (sz + 2047) // 2048:
                raise RuntimeError(name + ' grew but is not last file')
            o.seek(lba * 2048)
            o.write(data + b'\0' * (nsec * 2048 - len(data)))
            newtotal = max(newtotal, lba + nsec)
            # 디렉터리 레코드 크기
            o.seek(rec + 10); o.write(both32(len(data)))
        if newtotal > total:
            o.seek(newtotal * 2048 - 1); o.write(b'\0')
        o.seek(16 * 2048 + 80); o.write(both32(newtotal))
    return newtotal
