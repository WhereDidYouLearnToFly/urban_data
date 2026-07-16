"""Generic subscriber for gr-zeromq's native PDU wire format -- a single
PMT-serialized frame per message, as sent by zeromq_pub_msg_sink (see
grc/urban_data.grc: zmq_sink_0 on 5556 for Events, zmq_sink on 5557 for
agent_trigger group summaries). Mirrors zmq_source.py's plain-pyzmq style;
this hop stays inside GNU Radio's own wire format end to end, so recv()
unwraps PMT instead of forwarding a raw multipart payload.
"""
import pmt
import zmq


class ZmqPduSubscriberLogic:
    def __init__(self, address: str):
        self._ctx = zmq.Context()
        self._socket = self._ctx.socket(zmq.SUB)
        self._socket.connect(address)
        self._socket.setsockopt(zmq.SUBSCRIBE, b"")

    def recv(self) -> bytes:
        """Blocks until a message arrives. Returns the unwrapped PDU payload."""
        raw = self._socket.recv()
        pdu = pmt.deserialize_str(raw)
        return bytes(pmt.u8vector_elements(pmt.cdr(pdu)))

    def close(self):
        self._socket.close()
        self._ctx.term()
