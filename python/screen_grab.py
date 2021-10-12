# importing the required packages
import pyautogui
import cv2
import time
import numpy as np
import win32gui


def screen_grab(out_path,end):
    try:
        top_windows = []
        win32gui.EnumWindows(windowEnumerationHandler, top_windows)
        for i in top_windows:
            if "syntheyes pro" in i[1].lower():
                win32gui.ShowWindow(i[0], 5)
                win32gui.SetForegroundWindow(i[0])
                break

        # Specify resolution
        resolution = (1920, 1080)

        # Specify video codec
        codec = cv2.VideoWriter_fourcc(*"XVID")

        # Specify frames rate. We can choose any
        # value and experiment with it
        fps = 24.0

        # Creating a VideoWriter object
        out = cv2.VideoWriter(out_path, codec, fps, resolution)

        start_time = time.time() + end
        while True:

            if time.time() > start_time:
                break
            else:

                # Take screenshot using PyAutoGUI
                img = pyautogui.screenshot()

                # Convert the screenshot to a numpy array
                frame = np.array(img)

                # Convert it from BGR(Blue, Green, Red) to
                # RGB(Red, Green, Blue)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Write it to the output file
                out.write(frame)

        # Release the Video writer
        out.release()

        # Destroy all windows
        cv2.destroyAllWindows()
        return True

    except :
        return False


def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def play_back(outpath, hlev):
    cameras = [camera.Name() for camera in hlev.Cameras()]
    cam = hlev.FindObjByName(cameras[0])
    sht = cam.Get("shot")
    anim_start = hlev.AnimStart()
    anim_end = hlev.AnimEnd()
    frame_rate = sht.rate
    hlev.SetRoom("Coordinates")
    sleep_time = (anim_end - anim_start) / frame_rate
    hlev.SetFrame(anim_start)
    hlev.SetPlaybackRate(1.0)
    hlev.Play()
    result = screen_grab(outpath, sleep_time)
    if result:
        hlev.Stop()
        return True
    else:
        return False
