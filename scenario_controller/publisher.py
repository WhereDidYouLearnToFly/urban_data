import json
import zmq


class ZmqPublisher:
    TOPIC = b"urban_data"

    def __init__(self):
        self._ctx = zmq.Context()
        self._socket = None
        self._address = None

    def connect(self, address: str):
        if self._socket:
            self.disconnect()
        self._socket = self._ctx.socket(zmq.PUB)
        self._socket.bind(address)
        self._address = address

    def disconnect(self):
        if self._socket:
            self._socket.close()
            self._socket = None
            self._address = None

    def publish(self, event: dict):
        if not self._socket:
            return
        payload = json.dumps(event).encode()
        self._socket.send_multipart([self.TOPIC, payload])

    @property
    def address(self) -> str:
        return self._address or ""

    @property
    def connected(self) -> bool:
        return self._socket is not None

    def __del__(self):
        self.disconnect()
        self._ctx.term()
