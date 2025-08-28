import threading
import time
import math
from pynput import keyboard
import pyautogui

# ---------- parameters ----------
RADIUS = 100                    # pixels
SECONDS_PER_REV = 0.2           # the only speed control
MAX_FPS = None                  # visual smoothness cap; set to None to uncap
HOTKEY_TOGGLE = "<ctrl>+<alt>+m"
HOTKEY_QUIT   = "<ctrl>+<alt>+q"
# --------------------------------

run_lock = threading.Event()
motion_stop = threading.Event()

def run_circle_loop():
    """
    Cursor moves in a circle centered at start position.
    Revolution timing is driven solely by SECONDS_PER_REV.
    MAX_FPS only limits how often we send updates, not speed.
    """
    cx, cy = pyautogui.position()
    period = max(1e-3, float(SECONDS_PER_REV))  # avoid division by zero
    min_frame_interval = (1.0 / MAX_FPS) if (MAX_FPS and MAX_FPS > 0) else 0.0

    t0 = time.perf_counter()
    try:
        while not motion_stop.is_set():
            frame_start = time.perf_counter()

            # phase u in [0,1) determined by elapsed time and period
            u = ((frame_start - t0) / period) % 1.0

            theta = 2.0 * math.pi * u
            x = cx + RADIUS * math.cos(theta)
            y = cy + RADIUS * math.sin(theta)
            pyautogui.moveTo(x, y)

            if min_frame_interval > 0.0:
                sleep_for = min_frame_interval - (time.perf_counter() - frame_start)
                if sleep_for > 0:
                    time.sleep(sleep_for)
            else:
                # tiny yield to avoid 100% CPU if uncapped
                time.sleep(0.0005)
    finally:
        pyautogui.moveTo(cx, cy)

def toggle_motion():
    if run_lock.is_set():
        motion_stop.set()
        return

    def worker():
        run_lock.set()
        motion_stop.clear()
        try:
            run_circle_loop()
        finally:
            motion_stop.set()
            run_lock.clear()

    threading.Thread(target=worker, daemon=True).start()

def stop_all_and_quit():
    motion_stop.set()
    return False

def main():
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0

    print("Toggle loop:", HOTKEY_TOGGLE)
    print("Quit:       ", HOTKEY_QUIT)

    with keyboard.GlobalHotKeys({
        HOTKEY_TOGGLE: toggle_motion,
        HOTKEY_QUIT:   stop_all_and_quit,
    }) as h:
        h.join()

if __name__ == "__main__":
    main()
