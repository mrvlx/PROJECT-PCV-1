import cv2
import numpy as np


def bgr_ke_hsv(frame_bgr):
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

KALIBRASI_DEFAULT = {
    'merah': {
        'rentang_h': [[0, 12], [168, 179]],  # merah terbelah dua ujung
        's_min': 90,
        'v_min': 50,
    },
    'biru': {
        'rentang_h': [[100, 130]],
        's_min': 90,
        'v_min': 45,
    },
}


def deteksi_warna(H, S, V, kal):
    mask_pekat = (S >= kal['s_min']) & (V >= kal['v_min'])
    mask_hue = np.zeros(H.shape, dtype=bool)
    for h_min, h_max in kal['rentang_h']:
        mask_hue |= (H >= h_min) & (H <= h_max)
    return mask_hue & mask_pekat


def deteksi_merah(H, S, V, kal=None):
    kal = kal or KALIBRASI_DEFAULT['merah']
    return deteksi_warna(H, S, V, kal)


def deteksi_biru(H, S, V, kal=None):
    kal = kal or KALIBRASI_DEFAULT['biru']
    return deteksi_warna(H, S, V, kal)


def mask_ke_u8(mask_bool):
    return (mask_bool * 255).astype(np.uint8)


def deteksi_dua_tangan(frame_bgr, kalibrasi=None):
    kalibrasi = kalibrasi or KALIBRASI_DEFAULT
    hsv = bgr_ke_hsv(frame_bgr)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    merah = deteksi_merah(H, S, V, kalibrasi['merah'])
    biru = deteksi_biru(H, S, V, kalibrasi['biru'])
    return mask_ke_u8(merah), mask_ke_u8(biru)