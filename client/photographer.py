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
from rich.console import Group
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

SCREENSHOTS_DIR = Path("~/AppData/Roaming/.minecraft/screenshots").expanduser().resolve()
API_URL = "http://ec2-3-145-142-180.us-east-2.compute.amazonaws.com:8080/caption-image"
SIO = socketio.AsyncClient()


@dataclass
class DataStore:
    uuid: str = None
    uuid_event = asyncio.Event()
    screenshot_delay: int = None
    mc_window_id = None
    mc_window_title = None
    is_event_in_progress = False
    is_focused = False


DATA = DataStore()  # Global shared data

# Rich output stuff
CONSOLE = Console()
CONNECTION_LOADING = Status("[bright_red]Connecting to server")
FOCUS_LOADING = Status("[red]Minecraft not focused")


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


async def update_is_focused():
    cur_win_id = win32gui.FindWindow(None, get_foreground_window_title())
    DATA.is_focused = DATA.mc_window_id == cur_win_id
    if not DATA.is_focused:
        FOCUS_LOADING.update(f"[red]Minecraft not focused ('{DATA.mc_window_title}')")


@SIO.event
async def connect_error(data):
    CONSOLE.log(f"[bright_red]The connection failed! [{data}]")


@SIO.event
async def disconnect():
    if DATA.is_event_in_progress:
        CONSOLE.log("Screenshot in progress when shutting down!")
        await SIO.emit("screenshot_failed")
        DATA.is_event_in_progress = False

    DATA.uuid = None
    DATA.uuid_event.clear()
    await SIO.disconnect()
    CONSOLE.log("Client disconnected")


@SIO.event
async def uuid(data):
    DATA.uuid = data
    DATA.uuid_event.set()


@SIO.event
async def message(msg):
    CONSOLE.log(f"Message from server: {msg}")


@SIO.event
async def screenshot(obs_id, user_caption):
    CONSOLE.log(f"Received screenshot request: id={obs_id},caption='{user_caption}'")

    if not DATA.is_focused:
        CONSOLE.log("Minecraft not focused - failed to take a screenshot!")
        await SIO.emit("screenshot_failed", obs_id)
        return

    if DATA.is_event_in_progress:
        CONSOLE.log("Screenshot already in progress!")
        await SIO.emit("screenshot_failed", obs_id)
        return

    DATA.is_event_in_progress = True
    CONSOLE.log(
        f"Received screenshot request. Waiting {DATA.screenshot_delay} seconds to allow teleport to load"
    )
    # Give time for the picture to process
    await asyncio.sleep(DATA.screenshot_delay)

    pydirectinput.keyDown("f2")
    pydirectinput.keyUp("f2")

    # Give time for the picture to process
    await asyncio.sleep(2)

    CONSOLE.log("Grabbing most recent screenshot")
    ss_path = get_newest_screenshot()

    CONSOLE.log(f"Calling API with picture {ss_path}")
    data = await call_api(ss_path, user_caption)
    CONSOLE.log(f"response: {data}")

    CONSOLE.log("sending response to server")
    await SIO.emit(
        "screenshot_response",
        data={
            "clientUuid": DATA.uuid,
            "observationId": obs_id,
            "feedback": data["feedback"],
            "generatedCaption": data["generated caption"],
            "score": data["score"],
        },
    )
    DATA.is_event_in_progress = False


async def handle_gui(args):
    with Live(console=CONSOLE, refresh_per_second=10) as live_table:
        while True:
            await asyncio.sleep(0.1)
            await update_is_focused()
            live_table.update(
                Group(
                    f":white_check_mark:{args.host}:{args.port} \[[gray]{DATA.uuid}]"
                    if DATA.uuid is not None
                    else CONNECTION_LOADING,
                    f":white_check_mark:Focused ('{DATA.mc_window_title}')"
                    if DATA.is_focused
                    else FOCUS_LOADING,
                )
            )


async def main(args):
    asyncio.create_task(handle_gui(args))

    url = f"ws://{args.host}:{args.port}"
    CONSOLE.log(f"connecting to {url}")
    await SIO.connect(url, transports="websocket")

    # Wait for UUID to be set
    await DATA.uuid_event.wait()
    CONSOLE.log(f"UUID is {DATA.uuid}")

    # Free to do other stuff now
    await SIO.wait()


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

    CONSOLE.log("Focus your Minecraft window!")
    time.sleep(1)

    seconds = 3
    for ind in range(seconds):
        CONSOLE.log(seconds - ind)
        time.sleep(1)

    mc_window_title = get_foreground_window_title()
    mc_window_id = win32gui.FindWindow(None, mc_window_title)
    DATA.mc_window_id = mc_window_id
    DATA.mc_window_title = mc_window_title

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
    loop.close()
    ...
