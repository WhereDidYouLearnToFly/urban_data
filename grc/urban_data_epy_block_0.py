import os, sys
sys.path.insert(0, os.path.join("/home/radiolab9/github/urban_data/grc", os.pardir))

import pmt
from gnuradio import gr
from common.ai_analyzer import AnalyzerLogic

import numpy as np


class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self, name="ai_analyzer", in_sig=[], out_sig=[])
        self.logic = AnalyzerLogic()
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

    def handle_msg(self, msg):
        blob = bytes(pmt.u8vector_elements(pmt.cdr(msg)))
        out = self.logic.analyze(blob)
        out_pmt = pmt.init_u8vector(len(out), list(out))
        self.message_port_pub(pmt.intern("out"), pmt.cons(pmt.PMT_NIL, out_pmt))