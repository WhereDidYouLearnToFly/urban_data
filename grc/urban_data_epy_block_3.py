import os, sys, threading

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")

sys.path.insert(0, URBAN_DATA_ROOT)

import pmt
import zmq
from gnuradio import gr
from common.zmq_source import ZmqSourceLogic


class blk(gr.basic_block):
    def __init__(self, address="tcp://127.0.0.1:5555"):
        gr.basic_block.__init__(self, name="zmq_generic_input", in_sig=[], out_sig=[])
        self.message_port_register_out(pmt.intern("sources"))
        self.logic = ZmqSourceLogic(address)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            try:
                payload = self.logic.recv()
            except zmq.ZMQError:
                return
            pdu = pmt.init_u8vector(len(payload), list(payload))
            self.message_port_pub(pmt.intern("sources"), pmt.cons(pmt.PMT_NIL, pdu))

    def stop(self):
        self.logic.close()
        return True
