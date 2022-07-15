"""References

Sending key to inactive window
    https://stackoverflow.com/questions/12996985/send-some-keys-to-inactive-window-with-python


"""
import time

import socketio
import win32gui
import win32con
import win32api
import pydirectinput

from typing import Optional
from ctypes import windll, create_unicode_buffer

IS_FOCUSED = False


def get_foreground_window_title() -> Optional[str]:
    """https://stackoverflow.com/questions/10266281/obtain-active-window-using-python"""
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)

    return buf.value


def send_key(window_id, key, delay=0.5):
    """https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN"""
    win32api.SendMessage(window_id, win32con.WM_KEYDOWN, key, 0)
    time.sleep(delay)
    win32api.SendMessage(window_id, win32con.WM_KEYUP, key, 0)

    win32api.PostMessage(window_id, win32con.WM_KEYDOWN, key, 0)
    time.sleep(delay)
    win32api.PostMessage(window_id, win32con.WM_KEYUP, key, 0)


sio = socketio.Client()
sio.connect("ws://localhost:8234")


@sio.event
def connect():
    print("I'm connected!")


@sio.event
def connect_error(data):
    print(f"The connection failed! [{data}]")


@sio.event
def disconnect():
    print("I'm disconnected!")


@sio.event
def uuid(data):
    print(f"UUID: {data}")


@sio.event
def screenshot():
    if not IS_FOCUSED:
        print("FAILED TO TAKE SCREENSHOT!!")
        return

    print("Taking screenshot")

    pydirectinput.keyDown("f2")
    time.sleep(0.1)
    pydirectinput.keyUp("f2")

    # TODO: - Get screenshot file
    #       - Call API and get response
    #       - Send response back to server


print("Focus your Minecraft window!")
time.sleep(1)

seconds = 3
for ind in range(seconds):
    print(seconds - ind)
    time.sleep(1)

mc_window_title = get_foreground_window_title()
mc = win32gui.FindWindow(None, mc_window_title)
print(f"'{mc_window_title}' found with id [{mc}]")

while True:
    time.sleep(seconds)

    # input("take screenshot [enter]")

    cur_win_id = win32gui.FindWindow(None, get_foreground_window_title())
    IS_FOCUSED = cur_win_id == mc

    if not IS_FOCUSED:
        print("Minecraft not focused!!")

    # pydirectinput.keyDown('f2')
    # time.sleep(0.1)
    # pydirectinput.keyUp('f2')

    # print("attempting screenshot")

# send_key(mc, win32con.VK_F2)
# print(win32api.FormatMessage(win32api.GetLastError()))

# win32api.PostMessage(mc, win32con.WM_CHAR, 0x44, 0)

# def send_key(key):


# print('Go to minecraft!!!')
# time.sleep(3)
# send_key("f2")
