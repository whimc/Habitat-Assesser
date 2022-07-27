import requests
import json

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


def get_feedback():
    files = {"image": open(get_newest_screenshot(), "rb")}
    response = requests.post(
        API_URL,
        data={
            "user-caption": "Plain orange desert",
        },
        files=files,
    )

    data = json.loads(response.content)
    return Feedback(data["feedback"], data["generated caption"], data["score"])


feedback = get_feedback()
print(feedback)
