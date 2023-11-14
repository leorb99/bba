from r2a.ir2a import IR2A
from player.parser import *
import matplotlib.pyplot as plt
import statistics
import time
import math
from base.timer import Timer


class R2A_BBA1(IR2A):
    def __init__(self, id):
        IR2A.__init__(self, id)

        self.qi = []

        # How fast was our last chunk download in bps?
        self.capacity_estimation = 0
        self.safe_step_constant = 2

        self.last_request_time = None

        self.max_reservoir = 35
        self.min_reservoir: int = 2

        self.reservoir = 20
        self.upper_reservoir = 54

        self.rate_index: int = 0
        self.rate_index_min: int = 0
        self.rate_index_max: int = None

        self.buffer_size: int = 0

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())

        self.qi = self.parsed_mpd.get_qi()
        self.rate_index_max = len(self.qi) - 1

        self.last_request_time = time.time()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.buffer_size = self.whiteboard.get_amount_video_to_play()

        if self.buffer_size <= self.reservoir:
            self.rate_index = self.rate_index_min
        elif self.buffer_size >= self.upper_reservoir:
            self.rate_index = self.rate_index_max
        else:
            ideal_rate_index = (
                (self.buffer_size - self.reservoir) * self.rate_index_max
            ) / (self.upper_reservoir - self.reservoir)

            if self.capacity_estimation >= self.safe_step_constant * (self.rate_index + 1):
                self.rate_index = math.floor(ideal_rate_index)
            elif ideal_rate_index >= (self.rate_index + 1):
                self.rate_index = math.floor(ideal_rate_index)
            elif ideal_rate_index <= (self.rate_index - 1):
                self.rate_index = math.ceil(ideal_rate_index)

        self.last_request_time = time.perf_counter()

        msg.add_quality_id(self.qi[self.rate_index])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        # Estimate network capacity
        time_to_download = time.perf_counter() - self.last_request_time

        # In bits
        average_chunk_size = msg.get_quality_id()
        current_chunk_size = msg.get_bit_length()

        if current_chunk_size != 0:
            # The throughput of the last download in bits per second
            self.capacity_estimation = current_chunk_size / time_to_download

        # Make reservoir estimation
        target_reservoir = (2 * self.buffer_size) * (
            (average_chunk_size / self.capacity_estimation) - 1
        )

        self.reservoir = min(
            max(target_reservoir, self.min_reservoir), self.max_reservoir
        )

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

    @staticmethod
    def estimate_immediate_chunck_size():
        pass
