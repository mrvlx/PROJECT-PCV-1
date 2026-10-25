import pygame

def init_audio():
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


def play_bgm(path, volume=0.4):
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)  # loop
        pygame.mixer.music.set_volume(volume)
    except Exception as e:
        print(f"Gagal load BGM: {e}")


def play_sfx(path, volume=0.6):
    try:
        sfx = pygame.mixer.Sound(path)
        sfx.set_volume(volume)
        sfx.play()
    except Exception:
        pass  #