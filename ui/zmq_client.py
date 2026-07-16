"""Qt wrapper around common.zmq_pdu_subscriber.ZmqPduSubscriberLogic -- runs
the blocking recv() loop on a background thread and re-emits each decoded
PDU payload as a Qt signal on the GUI thread.
"""
import threading

import zmq
from PyQt5.QtCore import QObject, pyqtSignal

from common.zmq_pdu_subscriber import ZmqPduSubscriberLogic


class PduSubscriber(QObject):
    messageReceived = pyqtSignal(bytes)
    messageError = pyqtSignal(str)   # one malformed PDU -- socket is still alive
    disconnected = pyqtSignal(str)   # socket itself died, no more messages will arrive

    def __init__(self, address: str, parent=None):
        super().__init__(parent)
        self.logic = ZmqPduSubscriberLogic(address)
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._running:
            try:
                payload = self.logic.recv()
            except zmq.ZMQError as exc:
                if self._running:
                    self.disconnected.emit(str(exc))
                return
            except Exception as exc:
                if self._running:
                    self.messageError.emit(str(exc))
                continue
            self.messageReceived.emit(payload)

    def stop(self):
        self._running = False
        self.logic.close()
