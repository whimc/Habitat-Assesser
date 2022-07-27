import asyncio
import socketio

sio = socketio.Client(logger=True, engineio_logger=True)


@sio.event
def connect():
    print("connection established")


@sio.event
def disconnect():
    sio.disconnect()
    exit("disconnected from server")


@sio.event
def uuid(data):
    print(f"uuid: {data}")


if __name__ == "__main__":
    sio.connect("http://localhost:8234")
    sio.wait()
