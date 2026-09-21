import cv2
import numpy as np
import time


def gamma_correction(img, gamma=1.0):
    # P2: Power-law transformation, s = (r/255)^gamma
    # Pakai float biar ga overflow
    img_float = img.astype(np.float64) / 255.0
    out = np.power(img_float, gamma)
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def gaussian_kernel(size=3, sigma=1.0):
    # P3: Bikin kernel Gaussian manual
    ax = np.arange(-size // 2 + 1., size // 2 + 1.)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / kernel.sum()  # normalisasi biar jumlah = 1


def konvolusi2d_vektor(img, kernel):
    # P3: Konvolusi manual tapi vektorisasi (biar cepet)
    k = kernel.shape[0] // 2
    pad = np.pad(img.astype(np.float64), k, mode='edge')
    windows = np.lib.stride_tricks.sliding_window_view(pad, kernel.shape)
    kf = np.flipud(np.fliplr(kernel))  # flip 180 buat konvolusi
    out = np.sum(windows * kf, axis=(2, 3))
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    cap = cv2.VideoCapture(0)
    # Resolusi proses kecil biar cepet, tampil di-resize gede
    PROC_W, PROC_H = 120, 90
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, PROC_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PROC_H)
    
    DISP_W, DISP_H = 640, 480
    
    mode = 1
    gamma_val = 0.7
    blur_kernel = gaussian_kernel(size=3, sigma=0.8)
    fps_list = []
    
    while True:
        t0 = time.time()
        
        # P1: Ambil frame dari webcam
        ok, frame = cap.read()
        if not ok:
            break
        
        # Proses sesuai mode
        if mode == 1:
            display_proc = frame.copy()
            label = "P1: Asli"
            
        elif mode == 2:
            # P2: Gamma correction
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            display_proc = gamma_correction(gray, gamma=gamma_val)
            display_proc = cv2.cvtColor(display_proc, cv2.COLOR_GRAY2BGR)
            label = f"P2: Gamma {gamma_val:.2f}"
            
        elif mode == 3:
            # P3: Blur manual
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur_result = konvolusi2d_vektor(gray, blur_kernel)
            display_proc = cv2.cvtColor(blur_result, cv2.COLOR_GRAY2BGR)
            label = "P3: Blur 3x3"
            
        elif mode == 4:
            # Pipeline lengkap P1 -> P2 -> P3
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            terang = gamma_correction(gray, gamma=gamma_val)
            halus = konvolusi2d_vektor(terang, blur_kernel)
            display_proc = cv2.cvtColor(halus, cv2.COLOR_GRAY2BGR)
            label = "Pipeline P1->P2->P3"
        
        # Resize ke ukuran tampil
        display = cv2.resize(display_proc, (DISP_W, DISP_H), 
                             interpolation=cv2.INTER_LINEAR)
        
        # Hitung FPS
        dt = time.time() - t0
        fps_list.append(1.0 / max(dt, 1e-6))
        if len(fps_list) > 30:
            fps_list.pop(0)
        fps = np.mean(fps_list)
        
        # Tampilin label & FPS
        cv2.putText(display, label, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(display, f"FPS: {fps:.1f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        cv2.imshow("Dalang Bayangan - Minggu 1", display)
        
        # Handle input
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            break
        elif key == ord('1'):
            mode = 1
        elif key == ord('2'):
            mode = 2
        elif key == ord('3'):
            mode = 3
        elif key == ord('4'):
            mode = 4
        elif key == ord('+') or key == ord('='):
            gamma_val = min(3.0, gamma_val + 0.1)
        elif key == ord('-'):
            gamma_val = max(0.1, gamma_val - 0.1)
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()