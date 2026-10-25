import numpy as np


def gaussian_kernel(size=3, sigma=1.0):
    # Bobot Gauss, dinormalisasi biar jumlah = 1
    ax = np.arange(-size // 2 + 1., size // 2 + 1.)
    xx, yy = np.meshgrid(ax, ax)
    k = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return k / k.sum()


def konvolusi2d_cepat(img, kernel):
    # Konvolusi manual versi vektorisasi (sliding window)
    k = kernel.shape[0] // 2
    pad = np.pad(img.astype(np.float64), k, mode='edge')
    win = np.lib.stride_tricks.sliding_window_view(pad, kernel.shape)
    kf = np.flipud(np.fliplr(kernel))  # putar 180 = konvolusi
    out = np.sum(win * kf, axis=(2, 3))
    return np.clip(out, 0, 255).astype(np.uint8)


def blur_berwarna(frame_bgr, kernel):
    # blur per kanal BGR, jangan dijadin grayscale
    out = np.empty_like(frame_bgr)
    for c in range(3):
        out[:, :, c] = konvolusi2d_cepat(frame_bgr[:, :, c], kernel)
    return out