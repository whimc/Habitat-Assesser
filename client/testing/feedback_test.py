import socketio

from api_test import get_feedback

feedback = get_feedback()

sio = socketio.Client()
print("connecting")
sio.connect("ws://localhost:8234")

print("connected, sending response")

sio.emit(
    "screenshot_response",
    data={
        "clientUuid": "sample-uuid",
        "observationId": 1,
        "feedback": feedback.feedback,
        "generatedCaption": feedback.generated_caption,
        "score": feedback.score,
    },
    callback=lambda: print("received 1 by server"),
)

print("emit 1 done, sending another")

sio.emit(
    "screenshot_response",
    data={
        "client_uuid": "sample-uuid",
        "observation_id": 1,
        "feedback": feedback.feedback,
        "generated_caption": feedback.generated_caption,
        "score": feedback.score,
    },
    callback=lambda: print("received 2 by server"),
)

print("waiting")
sio.wait()
print("disconnecting")
sio.disconnect()
