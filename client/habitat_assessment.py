import json
import logging
import sys
import argparse
import asyncio
import aiohttp
import socketio
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from rich.console import Group
from rich.live import Live
from rich.console import Console
from rich.status import Status
@dataclass
class Args:
    host: str = "localhost"
    port: int = 8235
    api_url: str = "http://ec2-3-129-43-85.us-east-2.compute.amazonaws.com:8080/assess-habitat"
    log_file = None

@dataclass
class Habitat_Assessment:
    id: int
    user: str
    world: str
    teammates: str

@dataclass
class DataStore:
    uuid: Optional[str] = None
    uuid_event = asyncio.Event()

    assessment: Optional[Habitat_Assessment] = None
    @property
    def is_event_in_progress(self):
        return self.assessment is not None
DATA = DataStore()  # Global shared data
ARGS = Args()  # Global args
SIO = socketio.AsyncClient()
CONSOLE = Console()
CONNECTION_LOADING = Status("[bright_red]Connecting to server")
def my_excepthook(exc_type, exc_value, traceback):
    if exc_type == KeyboardInterrupt:
        log("Shutting down...")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(disconnect())
        exit()
    logging.error("Logging an uncaught exception", exc_info=(exc_type, exc_value, traceback))

sys.excepthook = my_excepthook


def log(msg):
    prefix = f"[aqua]assessment_id={DATA.assessment.id}[/]: " if DATA.assessment is not None else ""
    CONSOLE.log(f"{prefix}{msg}")
    logging.info(msg)

@SIO.event
async def connect_error(data):
    log(f"[bright_red]The connection failed! [{data}]")

async def assessment_failed(msg, id):
    log(f"[red]{msg}[/]")
    await SIO.emit("assessment_failed", id)

@SIO.event
async def disconnect():
    if DATA.is_event_in_progress:
        await assessment_failed("Assessment in progress while shutting down!", DATA.assessment.id)
        DATA.assessment = None

    DATA.uuid = None
    DATA.uuid_event.clear()
    await SIO.emit("disconnect")
    await SIO.disconnect()
    log("Client disconnected")


@SIO.event
async def uuid(data):
    DATA.uuid = data
    DATA.uuid_event.set()

async def call_api_habitat(assessment: Habitat_Assessment) -> dict:
    data = {
        "id": assessment.id,
        "user": assessment.user,
        "world": assessment.world,
        "teammates": assessment.teammates,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(ARGS.api_url, data=data) as resp:
            raw_data = await resp.content.read()
    return json.loads(raw_data)

@SIO.event
async def assess(assess_id, user_name, user_world, user_teammates):
    log(f"Received assessment request:\n assess_id = '{assess_id}'\n user = '{user_name}'\n world = '{user_world}'\n teammates = '{user_teammates}'")

    DATA.assessment = Habitat_Assessment(assess_id, user_name, user_world, user_teammates)

    log("Calling API")
    data = await call_api_habitat(DATA.assessment)
    log(f"Response from API: {data}")
    await SIO.emit(
        "assessment_response",
        data={
            "id": data["id"],
            "user": data["user"],
            "lowestCategory": data["lowestcategory"],
            "highestCategory": data["highestcategory"],
            "area": data["area"],
            "communicationsFacilities": data["communicationsfacilities"],
            "food": data["food"],
            "gravity": data["gravity"],
            "health": data["health"],
            "oxygenRegulation": data["oxygenregulation"],
            "powerGeneration": data["powergeneration"],
            "radiationProtection": data["radiationprotection"],
            "supplies": data["supplies"],
            "shape": data["shape"],
            "transportation": data["transportation"]
        },
    )
    log("[green]Response sent to server")

    DATA.assessment = None
async def handle_gui():
    with Live(console=CONSOLE, refresh_per_second=10) as live_table:
        while True:
            group = [
                # Server connection
                f":white_check_mark:{ARGS.host}:{ARGS.port} \[{DATA.uuid}]"
                if DATA.uuid is not None
                else CONNECTION_LOADING,
            ]

            await asyncio.sleep(0.1)
            live_table.update(Group(*group))
async def main():
    asyncio.create_task(handle_gui())

    url = f"ws://{ARGS.host}:{ARGS.port}"
    log(f"connecting to {url}")
    await SIO.connect(url, transports="websocket")

    # Wait for UUID to be set
    await DATA.uuid_event.wait()
    log(f"Received UUID {DATA.uuid}")

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
        default=8235,
    )
    parser.add_argument(
        "--api-url",
        default="http://ec2-3-145-142-180.us-east-2.compute.amazonaws.com:8080/assess-habitat",
    )
    parser.add_argument(
        "--log-file",
        default=Path(__file__).parent / "habitat_assessment.log",
        type=argparse.FileType("w"),
    )
    args = parser.parse_args()
    ARGS.__dict__.update(vars(args))
    logger = logging.basicConfig(
        filename=args.log_file,
        level=logging.DEBUG,
        format="[%(asctime)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
