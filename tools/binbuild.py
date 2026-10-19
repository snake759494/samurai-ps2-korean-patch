# 한글판 ISO(2048) 내용을 원본과 같은 MODE2/2352 BIN 으로 만든다 (바뀐 섹터만 EDC/ECC 재계산)
import os, shutil
import cdecc

SS = 2352


def build(src_bin, iso_path, out_bin):
    n_src = os.path.getsize(src_bin) // SS
    n_iso = os.path.getsize(iso_path) // 2048
    if n_iso != n_src:
        raise RuntimeError('sector count differs: %d vs %d' % (n_iso, n_src))
    shutil.copyfile(src_bin, out_bin)
    changed = 0
    with open(src_bin, 'rb') as s, open(iso_path, 'rb') as i, open(out_bin, 'r+b') as o:
        for k in range(n_src):
            raw = s.read(SS)
            data = i.read(2048)
            if raw[24:2072] != data:
                o.seek(k * SS)
                o.write(cdecc.build_form1(raw[12:16], raw[16:24], data))
                changed += 1
    return changed


def write_cue(bin_name, cue_path):
    with open(cue_path, 'w', encoding='ascii', newline='\r\n') as f:
        f.write('FILE "%s" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n' % bin_name)
