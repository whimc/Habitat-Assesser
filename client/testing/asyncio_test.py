import asyncio
import socketio

from dataclasses import dataclass


@dataclass
class UUIDStore:
    uuid: str = None
    event = asyncio.Event()


sio = socketio.AsyncClient()
# sio = socketio.AsyncClient(logger=True, engineio_logger=True)
UUID = UUIDStore()


@sio.event
async def uuid(data):
    UUID.uuid = data
    print(f"**** UUID is {data}")
    UUID.event.set()


@sio.event
async def message(msg):
    print(f"From server: {msg}")


@sio.event
async def connect():
    print("**** connected to server")


@sio.event
async def disconnect():
    print("**** disconnected from server")
    await sio.disconnect()
    exit()


async def run():
    print("**** Waiting to connect to server...")
    await sio.connect("ws://127.0.0.1:8234", transports="websocket")
    print(f"Connected, sid is {sio.sid}")

    # Wait for UUID to be set
    await UUID.event.wait()
    print(f"UUID is {UUID.uuid}")

    # Free to do other stuff now
    await sio.wait()


if __name__ == "__main__":
    # sid = asyncio.run(sio.connect("ws://localhost:8234"))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    # asyncio.run(run())
