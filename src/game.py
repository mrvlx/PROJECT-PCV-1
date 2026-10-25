import cv2
import numpy as np
import random
from src.overlay import load_png, tempel_png
from src.audio import play_sfx

class Partikel:
    def __init__(self, x, y, warna):
        self.x, self.y = x, y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-5, 1)
        self.life = 20
        self.warna = warna

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1

    def gambar(self, frame):
        cv2.circle(frame, (int(self.x), int(self.y)), 3, self.warna, -1)

class Musuh:
    def __init__(self, warna, layar_w, layar_h, tipe='biasa', kecepatan=2, path_png=None):
        self.warna = warna
        self.tipe = tipe
        self.x = layar_w + random.randint(20, 220)
        self.y = random.randint(60, layar_h - 60)
        self.kecepatan = kecepatan
        self.hidup = True
        self.umur = 0

        self.frames = []
        if path_png:
            for p in path_png:
                bgr, alpha = load_png(p)
                if bgr is not None:
                    self.frames.append((bgr, alpha))

        self.radius = 28
        if self.frames:
            self.radius = self.frames[0][0].shape[1] // 2

        if tipe == 'cakil':
            self.hp = 1
            self.kecepatan = kecepatan * 1.8
        elif tipe == 'tameng':
            self.hp = 2
            self.kecepatan = kecepatan * 0.7
        else:
            self.hp = 1

    def update(self):
        self.x -= self.kecepatan
        self.umur += 1

    def gambar(self, frame):
        if not self.hidup:
            return

        if self.frames:
            idx = (self.umur // 8) % len(self.frames)
            bgr, alpha = self.frames[idx]
            frame = tempel_png(frame, bgr, alpha, int(self.x), int(self.y))
        else:
            warna_bgr = (0, 0, 255) if self.warna == 'merah' else (255, 0, 0)
            cv2.circle(frame, (int(self.x), int(self.y)), self.radius, warna_bgr, -1)

        if self.tipe == 'tameng' and self.hp > 1:
            cv2.circle(frame, (int(self.x), int(self.y)), self.radius + 4, (255, 255, 255), 2)

    def sudah_lewat(self):
        return self.x < -self.radius

class Game:
    LUAS_SMASH = 1900
    SPEED_CRIT = 25
    CHARGE_MAX = 45

    def __init__(self, layar_w=800, layar_h=450, path_png_merah=None, path_png_biru=None):
        self.layar_w, self.layar_h = layar_w, layar_h
        self.path_png = {'merah': path_png_merah, 'biru': path_png_biru}
        self.reset()

    def reset(self):
        self.skor = 0
        self.nyawa = 3
        self.musuh = []
        self.partikel = []
        self.frame_count = 0
        self.game_over = False
        self.efek_hit = 0
        self.shake = 0
        self.combo = 0
        self.charge = 0
        self.prev = {'kanan': None, 'kiri': None}

    def spawn_interval(self):
        return max(35, 90 - self.skor // 20)

    def spawn_musuh(self):
        warna = random.choice(['merah', 'biru'])
        tipe = random.choices(['biasa', 'cakil', 'tameng'], weights=[60, 20, 20])[0]
        path = self.path_png.get(warna)
        self.musuh.append(Musuh(warna, self.layar_w, self.layar_h,
                                tipe, random.uniform(1.5, 3.0), path))

    def _kekuatan(self, tangan):
        if tangan is None: return 0, 0
        if tangan['luas'] > self.LUAS_SMASH: return 2, 75
        return 1, 45

    def _speed(self, nama, tangan):
        if tangan is None:
            self.prev[nama] = None
            return 0
        c = tangan['centroid']
        p = self.prev[nama]
        self.prev[nama] = c
        if p is None: return 0
        return ((c[0] - p[0])**2 + (c[1] - p[1])**2) ** 0.5

    def _serang(self, tangan, speed, musuh):
        dmg, radius = self._kekuatan(tangan)
        cx, cy = tangan['centroid']
        jarak = ((cx - musuh.x)**2 + (cy - musuh.y)**2) ** 0.5
        if jarak > radius + musuh.radius: return False, 0, False
        crit = speed > self.SPEED_CRIT
        return True, dmg * (2 if crit else 1), crit

    def _ledak(self, x, y, warna):
        bgr = (0, 0, 255) if warna == 'merah' else (255, 0, 0)
        for _ in range(12):
            self.partikel.append(Partikel(x, y, bgr))

    def update(self, kanan, kiri):
        if self.game_over: return
        self.frame_count += 1
        if self.efek_hit > 0: self.efek_hit -= 1
        if self.shake > 0: self.shake -= 1

        dk, _ = self._kekuatan(kanan)
        dl, _ = self._kekuatan(kiri)
        self.charge = self.charge + 1 if (dk == 2 and dl == 2) else 0
        
        if self.charge >= self.CHARGE_MAX:
            self.skor += 10 * len(self.musuh)
            for m in self.musuh: self._ledak(m.x, m.y, m.warna)
            self.musuh.clear()
            self.charge = 0
            self.efek_hit = 10
            self.shake = 10

        if self.frame_count % self.spawn_interval() == 0:
            self.spawn_musuh()

        vk = self._speed('kanan', kanan)
        vl = self._speed('kiri', kiri)

        for p in self.partikel[:]:
            p.update()
            if p.life <= 0: self.partikel.remove(p)

        for m in self.musuh[:]:
            m.update()
            kena, dmg, crit = False, 0, False
            
            if m.warna == 'biru' and kanan:
                kena, dmg, crit = self._serang(kanan, vk, m)
            elif m.warna == 'merah' and kiri:
                kena, dmg, crit = self._serang(kiri, vl, m)

            if kena:
                m.hp -= dmg
                if m.hp <= 0:
                    m.hidup = False
                    self.combo += 1
                    self.skor += 10 * (1 + self.combo // 4)
                    self._ledak(m.x, m.y, m.warna)
                    self.shake = 8 if crit else 4
                    play_sfx("assets/sounds/hit.wav")
                else:
                    self.efek_hit = 3

            if m.sudah_lewat():
                m.hidup = False
                self.nyawa -= 1
                self.combo = 0

            if not m.hidup: self.musuh.remove(m)

        if self.nyawa <= 0:
            self.game_over = True

    def gambar(self, frame):
        for p in self.partikel: p.gambar(frame)
        for m in self.musuh: m.gambar(frame)

        if self.efek_hit > 0:
            a = 0.15
            frame[:] = np.clip(a * 255 + (1 - a) * frame, 0, 255).astype(np.uint8)
        if self.shake > 0:
            frame = np.roll(frame, (random.randint(-3, 3), random.randint(-4, 4)), axis=(0, 1))

        cv2.putText(frame, f"Skor: {self.skor}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Nyawa: {self.nyawa}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if self.combo >= 3:
            cv2.putText(frame, f"COMBO x{1 + self.combo // 4}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if self.game_over:
            cv2.putText(frame, "GAME OVER", (self.layar_w // 2 - 80, self.layar_h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.putText(frame, f"Skor Akhir: {self.skor}", (self.layar_w // 2 - 90, self.layar_h // 2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, "Tekan R untuk restart", (self.layar_w // 2 - 120, self.layar_h // 2 + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        return frame