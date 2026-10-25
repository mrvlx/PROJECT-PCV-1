import numpy as np
import cv2


def erosi(mask, k=3):
    mask = np.asarray(mask, dtype=bool)
    r = k // 2
    pad = np.pad(mask, r, constant_values=False)  
    h, w = mask.shape
    out = np.ones((h, w), dtype=bool)
    for dy in range(k):
        for dx in range(k):
            out &= pad[dy:dy + h, dx:dx + w]
    return out


def dilasi(mask, k=3):
    mask = np.asarray(mask, dtype=bool)
    r = k // 2
    pad = np.pad(mask, r, constant_values=False)
    h, w = mask.shape
    out = np.zeros((h, w), dtype=bool)
    for dy in range(k):
        for dx in range(k):
            out |= pad[dy:dy + h, dx:dx + w]
    return out


def opening(mask, k=3):
    return dilasi(erosi(mask, k), k)


def closing(mask, k=3):
    return erosi(dilasi(mask, k), k)


def bersihkan_mask(mask, k=5):
    #opening dulu (buang bintik), baru closing (tutup lubang)
    m = opening(mask, k)
    m = closing(m, k)
    return m


# traking lewat connected components (materi P5) 
def labeling(mask_u8):
    n, label = cv2.connectedComponents(mask_u8.astype(np.uint8))
    return n, label


def ukur_objek(mask_u8, min_luas=80):
    n, label = labeling(mask_u8)
    objek = []
    for i in range(1, n):  
        ys, xs = np.where(label == i)
        luas = len(xs)
        if luas < min_luas:
            continue 
        objek.append({
            'label': i,
            'luas': int(luas),
            'centroid': (int(xs.mean()), int(ys.mean())),
            'bbox': (int(xs.min()), int(ys.min()),
                     int(xs.max() - xs.min() + 1),
                     int(ys.max() - ys.min() + 1)),
        })
    return sorted(objek, key=lambda o: o['luas'], reverse=True)


def lacak_tangan(mask_u8, min_luas=80):
    objek = ukur_objek(mask_u8, min_luas)
    return objek[0] if objek else None