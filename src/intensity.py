import numpy as np

def gamma_correction(img, gamma=1.0):
    #s = 255*(r/255)^gamma
    f = img.astype(np.float64) / 255.0
    out = np.power(f, gamma)
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def perbaiki_cahaya(hsv, gamma=0.7):
    hsv = hsv.copy()
    hsv[:, :, 2] = gamma_correction(hsv[:, :, 2], gamma)
    return hsv