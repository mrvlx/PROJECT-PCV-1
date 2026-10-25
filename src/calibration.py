import cv2
import numpy as np
import json
import os

try:
    from src.color import KALIBRASI_DEFAULT
except ImportError:
    from color import KALIBRASI_DEFAULT

NAMA_FILE = "kalibrasi.json"


def _statistik_roi(roi_hsv):
    H = roi_hsv[:, :, 0].ravel().astype(np.float64)
    S = roi_hsv[:, :, 1].ravel().astype(np.float64)
    V = roi_hsv[:, :, 2].ravel().astype(np.float64)
    valid = (S > 50) & (V > 50)
    return H[valid], S[valid], V[valid]


def kalibrasi_merah(roi_hsv):
    H, S, V = _statistik_roi(roi_hsv)
    if len(H) < 20:  
        return None
    bawah = H[H < 90]   
    atas = H[H >= 90]   
    rentang = []
    if len(bawah) > 0:
        rentang.append([0.0, float(np.percentile(bawah, 95))])
    if len(atas) > 0:
        rentang.append([float(np.percentile(atas, 5)), 179.0])
    return {
        'rentang_h': rentang,
        's_min': float(np.percentile(S, 5)),
        'v_min': float(np.percentile(V, 5)),
    }


def kalibrasi_biru(roi_hsv):
    H, S, V = _statistik_roi(roi_hsv)
    if len(H) < 20:
        return None
    return {
        'rentang_h': [[float(np.percentile(H, 8)), float(np.percentile(H, 92))]],
        's_min': float(np.percentile(S, 5)),
        'v_min': float(np.percentile(V, 5)),
    }


def simpan_kalibrasi(hasil, nama_file=NAMA_FILE):
    with open(nama_file, 'w') as f:
        json.dump(hasil, f, indent=2)


def muat_kalibrasi(nama_file=NAMA_FILE):
    if os.path.exists(nama_file):
        with open(nama_file) as f:
            return json.load(f)
    return None


def ambil_kalibrasi():
    kal = muat_kalibrasi()
    if kal is None:
        return KALIBRASI_DEFAULT
    return {
        'merah': kal.get('merah', KALIBRASI_DEFAULT['merah']),
        'biru': kal.get('biru', KALIBRASI_DEFAULT['biru']),
    }


def jalankan_kalibrasi():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: webcam ga bisa dibuka")
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)

    hasil = muat_kalibrasi() or {}

    print("=" * 45)
    print("KALIBRASI WARNA")
    print("  Masukin sarung tangan ke kotak, lalu tekan:")
    print("  [R] kalibrasi merah   [B] kalibrasi biru")
    print("  [S] simpan & selesai  [ESC] keluar tanpa simpan")
    print("=" * 45)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        frame_bersih = frame.copy()  

        h, w = frame.shape[:2]
        ukuran = min(w, h) // 3
        x1, y1 = w // 2 - ukuran // 2, h // 2 - ukuran // 2
        x2, y2 = w // 2 + ukuran // 2, h // 2 + ukuran // 2

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key in (ord('r'), ord('R')):
            hsv = cv2.cvtColor(frame_bersih, cv2.COLOR_BGR2HSV)
            kal = kalibrasi_merah(hsv[y1:y2, x1:x2])
            if kal:
                hasil['merah'] = kal
                print("Merah ok:", kal)
            else:
                print("Merah gagal: kotak kosong / gelap")
        elif key in (ord('b'), ord('B')):
            hsv = cv2.cvtColor(frame_bersih, cv2.COLOR_BGR2HSV)
            kal = kalibrasi_biru(hsv[y1:y2, x1:x2])
            if kal:
                hasil['biru'] = kal
                print("Biru ok:", kal)
            else:
                print("Biru gagal: kotak kosong / gelap")
        elif key in (ord('s'), ord('S')):
            if hasil:
                simpan_kalibrasi(hasil)
                print("Kalibrasi disimpan ke", NAMA_FILE)
            break

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        status = []
        if 'merah' in hasil:
            status.append("MERAH ok")
        if 'biru' in hasil:
            status.append("BIRU ok")
        teks = " ".join(status) if status else "belum ada kalibrasi"
        cv2.putText(frame, teks, (5, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        tampil = cv2.resize(frame, (800, 450))
        cv2.imshow("Kalibrasi", tampil)

    cap.release()
    cv2.destroyAllWindows()
    return hasil


# cara jalanin: python -m src.calibration
if __name__ == "__main__":
    jalankan_kalibrasi()