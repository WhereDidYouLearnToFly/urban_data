"""Generic ZMQ SUB bridge — plain pyzmq, no GNU Radio dependency.

Replaces gr-zeromq's zeromq_sub_msg_source, which only understands PMT-
serialized messages from another GNU Radio block. This lets any plain ZMQ
publisher (Scenario Controller today, real hardware sources later) feed the
flowgraph without linking against GNU Radio at all.
"""
import zmq


class ZmqSourceLogic:
    def __init__(self, address: str, topic: bytes = b""):
        self._ctx = zmq.Context()
        self._socket = self._ctx.socket(zmq.SUB)
        self._socket.connect(address)
        self._socket.setsockopt(zmq.SUBSCRIBE, topic)

    def recv(self) -> bytes:
        """Blocks until a message arrives. Returns the payload frame."""
        _topic, payload = self._socket.recv_multipart()
        return payload

    def close(self):
        self._socket.close()
        self._ctx.term()
