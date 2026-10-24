# DALANG ELEMEN

Dalang Elemen: mini game pengolahan citra yang mengubah tangan jadi senjata
elemen. Tangan kanan (merah) = Api/Bima, kiri (biru) = Air/Arjuna. Pilih
tangan tepat untuk kalahkan raksasa — salah warna, musuh lolos! Implementasi
pipeline P1-P5 dengan NumPy manual untuk mata kuliah Pengolahan Citra dan Video.

## Cara Main
- Sarung tangan merah di tangan kanan, biru (navy) di tangan kiri
- Musuh biru → serang pakai tangan kanan (merah)
- Musuh merah → serang pakai tangan kiri (biru)
- SPACE mulai/pause · R restart · C kalibrasi · Q keluar

## Jalankan
pip install -r requirements.txt
python -m src.calibration   # kalibrasi warna dulu (sekali aja)
python main.py              # main game
python debug_pipeline.py    # visualisasi per tahap (buat laporan)

## Pipeline
| Tahap | Materi | File |
|---|---|---|
| Akuisisi | P1 | src/acquisition.py |
| Gamma correction | P2 | src/intensity.py |
| Gaussian blur manual | P3 | src/filtering.py |
| Masking HSV | P4 | src/color.py |
| Morfologi + tracking | P5 | src/morphology.py |
| Logika game | - | src/game.py |

## Aturan Implementasi
- Semua operasi piksel manual NumPy
- OpenCV hanya untuk I/O, konversi warna, dan connected components
- Tanpa deep learning / model pre-trained