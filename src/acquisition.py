import cv2


def buka_kamera(index=0, lebar=160, tinggi=120):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise Exception("Tidak dapat membuka kamera")   
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, lebar)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, tinggi)
    return cap


def ambil_frame(cap):
    ok, frame = cap.read()
    if not ok:
        return None
    return frame