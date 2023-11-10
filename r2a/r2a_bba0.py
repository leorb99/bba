from r2a.ir2a import IR2A
from player.parser import *
import matplotlib.pyplot as plt
import time
from base.timer import Timer


class R2A_BBA0(IR2A):
    def __init__(self, id):
        IR2A.__init__(self, id)

        # C(t) is system capacity

        self.qi = []
        self.throughputs = []

        self.reservoir = 20
        self.upper_reservoir = 54

        self.rate_index: int = 0
        self.rate_index_min: int = 0
        self.rate_index_max: int = None

        self.buffer_size: int = 0
        self.max_buffer: int = 60

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())

        self.qi = self.parsed_mpd.get_qi()
        self.rate_index_max = len(self.qi) - 1

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.buffer_size = self.whiteboard.get_amount_video_to_play()
        print("buffer size", self.buffer_size)

        if self.buffer_size <= self.reservoir:
            self.rate_index = self.rate_index_min
        elif self.buffer_size >= self.upper_reservoir:
            self.rate_index = self.rate_index_max
        else:
            ideal_rate_index = (self.reservoir * self.rate_index_max) / (
                self.upper_reservoir - self.reservoir
            )

            if ideal_rate_index >= (self.rate_index + 1):
                self.rate_index += 1
            elif ideal_rate_index <= (self.rate_index - 1):
                self.rate_index -= 1

        msg.add_quality_id(self.qi[self.rate_index])

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
