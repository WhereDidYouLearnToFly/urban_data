import os, sys
sys.path.insert(0, os.path.join("/home/radiolab9/github/urban_data/grc", os.pardir))

import pmt
from gnuradio import gr
from common.ai_processor import ProcessorLogic


class blk(gr.basic_block):
    def __init__(self, scenario_path="/home/radiolab9/github/urban_data/scenarios/01_all_ok/scenario.json"):
        gr.basic_block.__init__(self, name="ai_processor", in_sig=[], out_sig=[])
        self.logic = ProcessorLogic(scenario_path)
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("events"))
        self.message_port_register_out(pmt.intern("agent_trigger"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

    def handle_msg(self, msg):
        blob = bytes(pmt.u8vector_elements(pmt.cdr(msg)))
        result = self.logic.handle(blob)
        for e in result["events"]:
            e_pmt = pmt.init_u8vector(len(e), list(e))
            self.message_port_pub(pmt.intern("events"), pmt.cons(pmt.PMT_NIL, e_pmt))
        for t in result["agent_triggers"]:
            t_pmt = pmt.init_u8vector(len(t), list(t))
            self.message_port_pub(pmt.intern("agent_trigger"), pmt.cons(pmt.PMT_NIL, t_pmt))