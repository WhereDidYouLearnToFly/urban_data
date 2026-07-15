import os, sys

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")

sys.path.insert(0, URBAN_DATA_ROOT)

import pmt
from gnuradio import gr
from common.debug_controller import DebugControllerLogic


class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self, name="debug_controller", in_sig=[], out_sig=[])
        self.logic = DebugControllerLogic()
        self.message_port_register_in(pmt.intern("events"))
        self.message_port_register_out(pmt.intern("print_pdu"))
        self.message_port_register_out(pmt.intern("store"))
        self.message_port_register_out(pmt.intern("print"))
        self.message_port_register_out(pmt.intern("log"))
        self.set_msg_handler(pmt.intern("events"), self.handle_msg)

    def handle_msg(self, msg):
        blob = bytes(pmt.u8vector_elements(pmt.cdr(msg)))
        result = self.logic.handle(blob)
        for port in ("print_pdu", "print", "log", "store"):
            data = result[port]
            if data is None:
                continue
            data_pmt = pmt.init_u8vector(len(data), list(data))
            self.message_port_pub(pmt.intern(port), pmt.cons(pmt.PMT_NIL, data_pmt))