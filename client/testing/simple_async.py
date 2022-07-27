import asyncio
import socketio

sio = socketio.AsyncClient(logger=True, engineio_logger=True)


@sio.event
async def connect():
    print("connection established")


@sio.event
async def disconnect():
    await sio.disconnect()
    print("disconnected from server")


@sio.event
async def uuid(data):
    print(f"uuid: {data}")


async def main():
    await sio.connect("ws://localhost:8234", transports="websocket")
    await sio.wait()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
