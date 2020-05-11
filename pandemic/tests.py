import time
from contextlib import contextmanager
import signal
from websocket import create_connection
import json


@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError


def send(command):
    ws.send(command)
    time.sleep(0.1)
    result = ws.recv()

    print(result)


# ws = create_connection("ws://127.0.0.1:8000/ws/pandemic/")
# send("/new")
room = "008fdbafebb16390"
ws = create_connection("ws://127.0.0.1:8000/ws/pandemic/" + room)
ws.recv()
# send(json.dumps("/role medecin"))
# send(json.dumps("/ready"))

send(json.dumps("/kick M.Beauchat"))
send(json.dumps("/join M.Beauchat"))
send(json.dumps("/move Miami"))
send(json.dumps("/move Atlanta"))
send(json.dumps("/move Atlanta"))
send(json.dumps("/move Miami"))
send(json.dumps("/end"))

send(json.dumps("/kick Casimir"))
send(json.dumps("/join Casimir"))
send(json.dumps("/move Miami"))
send(json.dumps("/move Atlanta"))
send(json.dumps("/move Atlanta"))
send(json.dumps("/move Miami"))
send(json.dumps("/end"))

send(json.dumps("/kick M.Beauchat"))
send(json.dumps("/join M.Beauchat"))
send(json.dumps("/move Miami"))
send(json.dumps("/move Atlanta"))
send(json.dumps("/move Atlanta"))
send(json.dumps("/move Miami"))
send(json.dumps("/end"))
# send(json.dumps("/dump Milan | Osaka"))


while True:
    with timeout(1):
        try:
            print(ws.recv())
        except TimeoutError:
            break

# send("/gamestate")
