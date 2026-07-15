import os, sys

URBAN_DATA_ROOT = os.path.join(os.path.expanduser("~"), "github", "urban_data")

sys.path.insert(0, URBAN_DATA_ROOT)

import pmt
from gnuradio import gr
from common.ai_analyzer import AnalyzerLogic

import numpy as np


class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self, name="ai_analyzer", in_sig=[], out_sig=[])
        self.logic = AnalyzerLogic()
        self.message_port_register_in(pmt.intern("sources"))
        self.message_port_register_out(pmt.intern("events"))
        self.set_msg_handler(pmt.intern("sources"), self.handle_msg)

    def handle_msg(self, msg):
        blob = bytes(pmt.u8vector_elements(pmt.cdr(msg)))
        out = self.logic.analyze(blob)
        out_pmt = pmt.init_u8vector(len(out), list(out))
        self.message_port_pub(pmt.intern("events"), pmt.cons(pmt.PMT_NIL, out_pmt))