# CD-ROM MODE2 Form1 섹터 EDC/ECC 생성 (ECMA-130)
import struct

_edc = []
for i in range(256):
    e = i
    for _ in range(8):
        e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
    _edc.append(e)
_f = [0] * 256
_b = [0] * 256
for i in range(256):
    j = (i << 1) ^ (0x11D if i & 0x80 else 0)
    _f[i] = j & 0xFF
    _b[i ^ j & 0xFF] = i


def edc(data):
    e = 0
    for x in data:
        e = (e >> 8) ^ _edc[(e ^ x) & 0xFF]
    return e


def _ecc_pq(sec, major, minor, mjm, mnm, out_off):
    size = major * minor
    for mj in range(major):
        index = (mj >> 1) * mjm + (mj & 1)
        a = b = 0
        for _ in range(minor):
            t = sec[0xC + index]
            index += mnm
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = _f[a]
        a = _b[_f[a] ^ b]
        sec[out_off + mj] = a
        sec[out_off + mj + major] = a ^ b


def build_form1(header4, subheader8, data2048):
    """2352 바이트 MODE2 Form1 섹터"""
    sec = bytearray(2352)
    sec[0:12] = b'\x00' + b'\xff' * 10 + b'\x00'
    sec[12:16] = header4
    sec[16:24] = subheader8
    sec[24:24 + 2048] = data2048
    struct.pack_into('<I', sec, 2072, edc(sec[16:2072]))
    # ECC 계산 시 헤더(주소)는 0으로 간주
    save = bytes(sec[12:16])
    sec[12:16] = b'\0\0\0\0'
    _ecc_pq(sec, 86, 24, 2, 86, 0x81C)
    _ecc_pq(sec, 52, 43, 86, 88, 0x8C8)
    sec[12:16] = save
    return bytes(sec)
