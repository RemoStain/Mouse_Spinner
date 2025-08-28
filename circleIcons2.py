import threading
import time
import math
from pynput import keyboard
import pyautogui

# ---------- parameters ----------
START_RADIUS = 350               # maximum radius in pixels
SHRINK_PER_SEC = 100              # shrink/grow speed in pixels per second
BASE_SECONDS_PER_REV = 1.0       # revolution time at START_RADIUS
MAX_FPS = None                    # cap on updates; None = uncapped
LOOP_MODE = True                 # True = repeat spiral in/out, False = once only
HOTKEY_TOGGLE = "<ctrl>+<alt>+m"
HOTKEY_QUIT   = "<ctrl>+<alt>+q"
# --------------------------------

run_lock = threading.Event()
motion_stop = threading.Event()

def run_spiral_loop():
    # Fix center once
    cx, cy = pyautogui.position()
    frame_interval = (1.0 / MAX_FPS) if (MAX_FPS and MAX_FPS > 0) else 0.0

    theta = 0.0  # carry across cycles

    def spiral_in_out(theta_start):
        radius = float(START_RADIUS)
        theta = theta_start

        # inward
        while not motion_stop.is_set() and radius > 0:
            now = time.perf_counter()
            seconds_per_rev = BASE_SECONDS_PER_REV * (radius / START_RADIUS if radius > 0 else 0.001)
            dtheta = (2.0 * math.pi / seconds_per_rev) * (frame_interval or 0.001)
            theta += dtheta

            pyautogui.moveTo(
                int(round(cx + radius * math.cos(theta))),
                int(round(cy + radius * math.sin(theta)))
            )

            radius = max(0.0, radius - SHRINK_PER_SEC * (frame_interval or 0.001))

            if frame_interval > 0.0:
                sleep_for = frame_interval - (time.perf_counter() - now)
                if sleep_for > 0:
                    time.sleep(sleep_for)
            else:
                time.sleep(0.0005)

        # outward
        while not motion_stop.is_set() and radius < START_RADIUS:
            now = time.perf_counter()
            seconds_per_rev = BASE_SECONDS_PER_REV * (radius / START_RADIUS if radius > 0 else 0.001)
            dtheta = (2.0 * math.pi / seconds_per_rev) * (frame_interval or 0.001)
            theta += dtheta

            pyautogui.moveTo(
                int(round(cx + radius * math.cos(theta))),
                int(round(cy + radius * math.sin(theta)))
            )

            radius = min(START_RADIUS, radius + SHRINK_PER_SEC * (frame_interval or 0.001))

            if frame_interval > 0.0:
                sleep_for = frame_interval - (time.perf_counter() - now)
                if sleep_for > 0:
                    time.sleep(sleep_for)
            else:
                time.sleep(0.0005)

        return theta  # hand back the final angle

    if LOOP_MODE:
        while not motion_stop.is_set():
            theta = spiral_in_out(theta)
        # leave wherever it ends
    else:
        theta = spiral_in_out(theta)

    # always return to center when stopped
    pyautogui.moveTo(cx, cy)


def toggle_motion():
    if run_lock.is_set():
        motion_stop.set()
        return

    def worker():
        run_lock.set()
        motion_stop.clear()
        try:
            run_spiral_loop()
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
    print("Toggle spiral:", HOTKEY_TOGGLE)
    print("Quit:         ", HOTKEY_QUIT)
    print("Loop mode:    ", LOOP_MODE)

    with keyboard.GlobalHotKeys({
        HOTKEY_TOGGLE: toggle_motion,
        HOTKEY_QUIT:   stop_all_and_quit,
    }) as h:
        h.join()

if __name__ == "__main__":
    main()
