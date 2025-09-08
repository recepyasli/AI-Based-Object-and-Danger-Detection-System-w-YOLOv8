import threading
import pygame
import time

def play_alert(path, volume=0.8, duration=2):
    def _play():
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            time.sleep(duration)
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"[AUDIO ERROR] {e}")

    threading.Thread(target=_play, daemon=True).start()