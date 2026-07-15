#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Urban Data Demo Flowgraph
# Description: Urban Data demo flowgraph -- ZMQ source, Fake AI Analyzer, Fake AI Processor, ZMQ stub sink
# GNU Radio version: 3.10.9.2

from gnuradio import blocks, gr
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import urban_data_epy_block_0 as epy_block_0  # embedded python block
import urban_data_epy_block_1 as epy_block_1  # embedded python block
import urban_data_epy_block_2 as epy_block_2  # embedded python block




class urban_data(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Urban Data Demo Flowgraph", catch_exceptions=True)

        ##################################################
        # Blocks
        ##################################################

        self.zmq_source = zeromq.sub_msg_source('tcp://127.0.0.1:5555', 100, False)
        self.zmq_sink_0 = zeromq.pub_msg_sink('tcp://127.0.0.1:5556', 100, True)
        self.zmq_sink = zeromq.pub_msg_sink('tcp://127.0.0.1:5557', 100, True)
        self.message_debug_0 = blocks.message_debug(True, gr.log_levels.info)
        self.epy_block_2 = epy_block_2.blk()
        self.epy_block_1 = epy_block_1.blk(scenario_path='/home/radiolab9/github/urban_data/scenarios/01_all_ok/scenario.json')
        self.epy_block_0 = epy_block_0.blk()
        self.epy_block_0.set_block_alias("AI_Analyzer")


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0, 'events'), (self.epy_block_1, 'events'))
        self.msg_connect((self.epy_block_0, 'events'), (self.epy_block_2, 'events'))
        self.msg_connect((self.epy_block_0, 'events'), (self.zmq_sink_0, 'in'))
        self.msg_connect((self.epy_block_1, 'agent_trigger'), (self.zmq_sink, 'in'))
        self.msg_connect((self.epy_block_2, 'print_pdu'), (self.message_debug_0, 'print_pdu'))
        self.msg_connect((self.epy_block_2, 'store'), (self.message_debug_0, 'store'))
        self.msg_connect((self.epy_block_2, 'log'), (self.message_debug_0, 'log'))
        self.msg_connect((self.epy_block_2, 'print'), (self.message_debug_0, 'print'))
        self.msg_connect((self.zmq_source, 'out'), (self.epy_block_0, 'sources'))





def main(top_block_cls=urban_data, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
