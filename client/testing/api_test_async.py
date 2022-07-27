import json
import asyncio
import aiohttp

from pathlib import Path
from dataclasses import dataclass

SCREENSHOTS_DIR = Path("~/AppData/Roaming/.minecraft/screenshots").expanduser().resolve()
API_URL = "http://ec2-3-145-142-180.us-east-2.compute.amazonaws.com:8080/caption-image"


@dataclass
class Feedback:
    feedback: str
    generated_caption: str
    score: float


def get_newest_screenshot() -> Path:
    paths = [path for path in SCREENSHOTS_DIR.iterdir() if path.is_file()]
    return max(paths, key=lambda f: f.stat().st_ctime)


async def get_feedback():
    data = {
        "user-caption": "Lots of trees from the warm climate",
        "image": open(get_newest_screenshot(), "rb"),
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=data) as resp:
            raw_data = await resp.content.read()

    data = json.loads(raw_data)
    return Feedback(data["feedback"], data["generated caption"], data["score"])


loop = asyncio.get_event_loop()
feedback = loop.run_until_complete(get_feedback())
print(feedback)
