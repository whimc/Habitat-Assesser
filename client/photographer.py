"""References

Sending key to inactive window
    https://stackoverflow.com/questions/12996985/send-some-keys-to-inactive-window-with-python


"""
import time
import json
import asyncio
import aiohttp
import time
import argparse

import socketio
import win32gui
import pydirectinput

from typing import Optional
from ctypes import windll, create_unicode_buffer
from pathlib import Path
from dataclasses import dataclass

SCREENSHOTS_DIR = Path("~/AppData/Roaming/.minecraft/screenshots").expanduser().resolve()
API_URL = "http://ec2-3-145-142-180.us-east-2.compute.amazonaws.com:8080/caption-image"


@dataclass
class DataStore:
    uuid: str = None
    uuid_event = asyncio.Event()
    is_focused = False
    screenshot_delay: int = None


DATA = DataStore()  # Global shared data


def get_foreground_window_title() -> Optional[str]:
    """https://stackoverflow.com/questions/10266281/obtain-active-window-using-python"""
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)

    return buf.value


def get_newest_screenshot() -> Path:
    paths = [path for path in SCREENSHOTS_DIR.iterdir() if path.is_file()]
    return max(paths, key=lambda path: path.stat().st_ctime)


async def call_api(screenshot_path: Path, user_caption: str) -> dict:
    data = {"user-caption": user_caption, "image": open(screenshot_path, "rb")}
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=data) as resp:
            raw_data = await resp.content.read()
    return json.loads(raw_data)


# TODO use asyncio
sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("I'm connected!")


@sio.event
async def connect_error(data):
    print(f"The connection failed! [{data}]")


@sio.event
async def disconnect():
    print("I'm disconnected!")
    DATA.uuid = None
    DATA.uuid_event.clear()

    await DATA.uuid_event.wait()
    print(f"new uuid: {DATA.uuid}")


@sio.event
async def uuid(data):
    DATA.uuid = data
    DATA.uuid_event.set()


@sio.event
async def message(msg):
    print(f"Message from server: {msg}")


@sio.event
async def screenshot(obs_id, user_caption):
    if not DATA.is_focused:
        print("Minecraft not focused - failed to take a screenshot!")
        await sio.emit("screenshot_failed")
        return

    print(
        f"Received screenshot request. Waiting {DATA.screenshot_delay} seconds to allow teleport to load"
    )
    # Give time for the picture to process
    await asyncio.sleep(DATA.screenshot_delay)

    pydirectinput.keyDown("f2")
    pydirectinput.keyUp("f2")

    # Give time for the picture to process
    await asyncio.sleep(2)

    print("Grabbing most recent screenshot")
    ss_path = get_newest_screenshot()

    print(f"Calling API with picture {ss_path}")
    data = await call_api(ss_path, user_caption)
    print(f"response: {data}")

    print("sending response to server")
    await sio.emit(
        "screenshot_response",
        data={
            "clientUuid": DATA.uuid,
            "observationId": obs_id,
            "feedback": data["feedback"],
            "generatedCaption": data["generated caption"],
            "score": data["score"],
        },
    )


async def ensure_focus():
    while True:
        await asyncio.sleep(1)

        cur_win_id = win32gui.FindWindow(None, get_foreground_window_title())
        DATA.is_focused = cur_win_id == mc

        if not DATA.is_focused:
            print("Minecraft not focused!")


async def main(host: str, port: int):
    asyncio.create_task(ensure_focus())

    await sio.connect(f"ws://{host}:{port}", transports="websocket")
    print(f"Connected, sid is {sio.sid}")

    # Wait for UUID to be set
    await DATA.uuid_event.wait()
    print(f"UUID is {DATA.uuid}")

    # Free to do other stuff now
    await sio.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default="localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8234,
    )
    parser.add_argument(
        "--screenshot-delay",
        type=int,
        help="Seconds to wait between teleporting and taking a screenshot.",
        default=15,
    )
    args = parser.parse_args()

    DATA.screenshot_delay = args.screenshot_delay

    print("Focus your Minecraft window!")
    time.sleep(1)

    seconds = 3
    for ind in range(seconds):
        print(seconds - ind)
        time.sleep(1)

    mc_window_title = get_foreground_window_title()
    mc = win32gui.FindWindow(None, mc_window_title)
    print(f"'{mc_window_title}' found with id [{mc}]")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.host, args.port))
    loop.close()
    ...
