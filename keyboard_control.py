import threading
import sys
import time

class KeyboardControl:
    def __init__(self, show_buffer, show_timestamp, pause_sending, resume_sending):
        self.show_buffer = show_buffer
        self.show_timestamp = show_timestamp
        self.pause_sending = pause_sending
        self.resume_sending = resume_sending
        self.paused = threading.Event()
        self.paused.set()  # Initially not paused
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def listen(self):
        while self.running:
            try:
                key = self.get_key()
                if key == 'b':
                    self.show_buffer()
                elif key == 't':
                    self.show_timestamp()
                elif key == 'p':
                    with self.lock:
                        self.paused.clear()
                    self.pause_sending()
                elif key == 'r':
                    with self.lock:
                        self.paused.set()
                    self.resume_sending()
            except Exception:
                time.sleep(0.1)

    def get_key(self):
        # Windows only: use msvcrt
        import msvcrt
        if msvcrt.kbhit():
            return msvcrt.getwch()
        time.sleep(0.1)
        return None

    def is_paused(self):
        return not self.paused.is_set()

    def stop(self):
        self.running = False
        self.thread.join()
