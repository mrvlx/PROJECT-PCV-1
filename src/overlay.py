import cv2
import numpy as np


def load_png(path, hapus_putih=True):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None, None

    if img.shape[2] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3].astype(np.float64) / 255.0
    else:
        # png tanpa alpha: piksel putih jadi transparan
        bgr = img
        if hapus_putih:
            B = bgr[:, :, 0].astype(np.int32)
            G = bgr[:, :, 1].astype(np.int32)
            R = bgr[:, :, 2].astype(np.int32)
            putih = (R > 235) & (G > 235) & (B > 235)
            alpha = np.where(putih, 0.0, 1.0)
        else:
            alpha = np.ones(bgr.shape[:2], dtype=np.float64)

    return bgr, alpha


def alpha_blend_manual(foreground_bgr, alpha_mask, background):
    fg = foreground_bgr.astype(np.float64)
    bg = background.astype(np.float64)

    if alpha_mask.ndim == 2:
        a = alpha_mask[:, :, np.newaxis]
    else:
        a = alpha_mask

    # rumus P4: hasil = a*depan + (1-a)*belakang
    hasil = a * fg + (1.0 - a) * bg
    return np.clip(hasil, 0, 255).astype(np.uint8)


def tempel_png(frame, png_bgr, png_alpha, cx, cy):
    if png_bgr is None:
        return frame

    h, w = png_bgr.shape[:2]
    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = x1 + w, y1 + h

    frame_h, frame_w = frame.shape[:2]

    # biar ga error kalau png kena tepi layar
    valid_x1 = max(0, x1)
    valid_y1 = max(0, y1)
    valid_x2 = min(frame_w, x2)
    valid_y2 = min(frame_h, y2)

    if valid_x1 >= valid_x2 or valid_y1 >= valid_y2:
        return frame

    bg_area = frame[valid_y1:valid_y2, valid_x1:valid_x2]

    px1 = valid_x1 - x1
    py1 = valid_y1 - y1
    px2 = px1 + (valid_x2 - valid_x1)
    py2 = py1 + (valid_y2 - valid_y1)

    fg_area = png_bgr[py1:py2, px1:px2]
    alpha_area = png_alpha[py1:py2, px1:px2]

    frame[valid_y1:valid_y2, valid_x1:valid_x2] = alpha_blend_manual(
        fg_area, alpha_area, bg_area)
    return frame