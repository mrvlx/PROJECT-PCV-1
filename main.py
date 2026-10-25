import cv2
import numpy as np
import time

from src.acquisition import buka_kamera, ambil_frame
from src.intensity import perbaiki_cahaya
from src.filtering import gaussian_kernel, blur_berwarna
from src.color import bgr_ke_hsv, deteksi_merah, deteksi_biru, mask_ke_u8
from src.morphology import bersihkan_mask, lacak_tangan
from src.calibration import ambil_kalibrasi, jalankan_kalibrasi
from src.game import Game
from src.overlay import load_png, tempel_png, alpha_blend_manual
from src.audio import init_audio, play_bgm

PROC_W, PROC_H = 160, 90
DISP_W, DISP_H = 800, 450

def load_background(path, w, h):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    img = cv2.resize(img, (w, h))
    if img.shape[2] == 4:
        # png transparan: komposit ke hitam pakai rumus P4
        bgr = img[:, :, :3]
        a = img[:, :, 3].astype(np.float64) / 255.0
        img = alpha_blend_manual(bgr, a, np.zeros((h, w, 3), dtype=np.uint8))
    return img


def background_fallback(w, h):
    # gradasi emas-coklat ala kelir, dipakai kalau kelir.png belum ada
    grad = np.linspace(0.35, 1.0, h).reshape(h, 1)
    bg = np.zeros((h, w, 3), dtype=np.float64)
    bg[:, :, 0] = 20 * grad    # B
    bg[:, :, 1] = 90 * grad    # G
    bg[:, :, 2] = 160 * grad   # R
    return bg.astype(np.uint8)

def pra_proses(frame_bgr, gamma_val, kernel):
    hsv = bgr_ke_hsv(frame_bgr)
    hsv = perbaiki_cahaya(hsv, gamma_val)
    prep = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return blur_berwarna(prep, kernel)

def deteksi_dan_bersihkan(frame_prep, morph_k, kalibrasi):
    hsv = bgr_ke_hsv(frame_prep)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    merah = mask_ke_u8(deteksi_merah(H, S, V, kalibrasi['merah']))
    biru = mask_ke_u8(deteksi_biru(H, S, V, kalibrasi['biru']))
    merah = mask_ke_u8(bersihkan_mask(merah > 0, morph_k))
    biru = mask_ke_u8(bersihkan_mask(biru > 0, morph_k))
    return merah, biru

def skala_ke_display(tangan):
    if tangan is None: return None
    sx, sy = DISP_W / PROC_W, DISP_H / PROC_H
    cx, cy = tangan['centroid']
    x, y, w, h = tangan['bbox']
    return {
        'luas': tangan['luas'],
        'centroid': (int(cx * sx), int(cy * sy)),
        'bbox': (int(x * sx), int(y * sy), int(w * sx), int(h * sy)),
    }

def gambar_wayang(frame, tangan, png_bgr, png_alpha, nama):
    if tangan is None: return frame
    cx, cy = tangan['centroid']
    frame = tempel_png (frame, png_bgr, png_alpha, cx, cy)
    cv2.putText(frame, nama, (cx - 20, cy - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame

def main():
    cap = buka_kamera(0, PROC_W, PROC_H)
    kernel = gaussian_kernel(3, 0.8)
    gamma_val = 0.7
    morph_k = 5
    kalibrasi = ambil_kalibrasi()

    bg = load_background("assets/backgrounds/kelir.png", DISP_W, DISP_H)
    if bg is None:
        print("kelir.png ga ketemu, pakai background gradasi")
        bg = background_fallback(DISP_W, DISP_H)

    wayang_merah_bgr, wayang_merah_alpha = load_png("assets/wayang/bima.png")
    wayang_biru_bgr, wayang_biru_alpha = load_png("assets/wayang/arjuna.png")
    
    init_audio()
    play_bgm("assets/sounds/bgm_gamelan.mp3")

    game = Game(
        DISP_W, DISP_H, 
        path_png_merah=["assets/enemies/merah_1.png", "assets/enemies/merah_2.png"],
        path_png_biru=["assets/enemies/biru_1.png", "assets/enemies/biru_2.png"]
    )
    
    fps_list = []
    paused = True

    print("DALANG ELEMEN - Versi Wayang & Audio")
    print("[SPACE] mulai/pause  [R] restart  [C] kalibrasi  [Q] keluar")

    while True:
        t0 = time.time()
        frame = ambil_frame(cap)
        if frame is None: break
        frame = cv2.flip(frame, 1)

        prep = pra_proses(frame, gamma_val, kernel)
        merah, biru = deteksi_dan_bersihkan(prep, morph_k, kalibrasi)
        kanan = skala_ke_display(lacak_tangan(merah))
        kiri = skala_ke_display(lacak_tangan(biru))

        display = bg.copy()
        
        display = gambar_wayang(display, kanan, wayang_merah_bgr, wayang_merah_alpha, "BIMA")
        display = gambar_wayang(display, kiri, wayang_biru_bgr, wayang_biru_alpha, "ARJUNA")

        if not paused and not game.game_over:
            game.update(kanan, kiri)
        display = game.gambar(display)

        prev_small = cv2.resize(frame, (200, 113))
        display[DISP_H - 121:DISP_H - 8, DISP_W - 208:DISP_W - 8] = prev_small
        cv2.rectangle(display, (DISP_W - 209, DISP_H - 122),
                      (DISP_W - 8, DISP_H - 8), (255, 255, 255), 1)

        dt = time.time() - t0
        fps_list.append(1.0 / max(dt, 1e-6))
        if len(fps_list) > 30: fps_list.pop(0)
        cv2.putText(display, f"FPS: {np.mean(fps_list):.1f}", (DISP_W - 110, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

        if paused and not game.game_over:
            cv2.putText(display, "PRESS SPACE TO START", (DISP_W // 2 - 160, DISP_H // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        cv2.imshow("Dalang Elemen", display)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')): break
        elif key == ord(' '): paused = not paused
        elif key == ord('r'): 
            game.reset()
            paused = False
        elif key == ord('c'):
            cap.release()
            cv2.destroyAllWindows()
            jalankan_kalibrasi()
            cap = buka_kamera(0, PROC_W, PROC_H)
            kalibrasi = ambil_kalibrasi()
        elif key in (ord('+'), ord('=')): gamma_val = min(3.0, gamma_val + 0.1)
        elif key == ord('-'): gamma_val = max(0.1, gamma_val - 0.1)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()