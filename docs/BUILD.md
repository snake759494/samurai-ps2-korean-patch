# 재빌드 절차

## 준비물
- Python 3.11 이상, `pip install numpy pillow scipy fonttools capstone`
- 원본 `Samurai (Japan, Asia).bin` (README 의 해시와 일치)
- 글꼴: `NanumSquareNeo-cBd.ttf`, `NanumSquareNeo-dEb.ttf`, `SeoulHangangB.ttf`, `SeoulHangangM.ttf`
- 번역 자료 `translation/` (저장소에는 포함하지 않음):
  - `script_ja.json` (원문 목록, `tools/scr.py` 로 추출), `script_ko_*.tsv` (번호→번역)
  - `elf_ja.tsv` (`tools/elf_dump.py` 로 추출), `elf_ko.tsv` (오프셋→번역)
  - `img_ko.tsv`, `img8_ko.tsv` (그림 글자 영역·번역)

## 폴더 배치
```
작업폴더/
  Samurai (Japan, Asia).bin
  *.ttf
  tools/
  translation/
```

## 빌드
```
python tools/build.py
```
- `work/` 에 VOLUME.DAT·SLPS_201.78 을 자동 추출하고, 글꼴·스크립트·실행 파일·그림을 바꿔 `Samurai (Korean).iso` 를 만듭니다.
- 바뀐 파일은 VOLUME.DAT 안의 **원래 자리에 들어가야 합니다.** 끝으로 옮겨지면 게임이 부팅 중 멈추므로, 빌드 결과의 `VOLUME.DAT 크기`가 원본(144,802,547)과 같은지 확인하세요.
- `python tools/check_text.py` 로 누락·줄 폭을 검사합니다.

## 패치 만들기
```
xdelta3 -e -0 -f -B 671088640 -s "Samurai (Japan, Asia).bin" "Samurai (Korean).iso" Samurai_PS2_KO_v1.0.xdelta
```

## 와이드 패치
한글판 실행 파일의 CRC(32비트 단위 XOR)를 계산해 `SLPS-20178_<CRC>.pnach` 로 이름을 바꿉니다. 실행 파일 문자열을 바꿀 때마다 CRC 가 달라집니다.
