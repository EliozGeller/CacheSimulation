from TrafficGenerator.CDFGenerator import Utils
import numpy as np

class ThresholdFlowletGenerator(object):
    def __init__(self, inter_arrival_time, break_to_message_n):
        """
        :param inter_arrival_time: Function for interarrival time between messages
        :param break_to_message_p: Breaking flow to 'break_to_message_n messages if flow size will be generated with
        probability that is > p
        :param break_to_message_n: Breaking flow to 'break_n_messages'
        """
        self.inter_arrival_time = inter_arrival_time
        self.break_threshold = 25  # 25 packets
        self.break_to_message_n = break_to_message_n

    def generate_flowlet_from_flow(self, flow) -> list:
        src_ip, dst_ip, flow_size, time, flow_id = flow
        if flow_size <= self.break_threshold:
            return [(src_ip, dst_ip, flow_size, time, str(flow_id) + ".0")]  # do not break flow to messaged
        else:
            flowlet_burst = []
            count = 0
            curr_time = time
            for i in range(self.break_to_message_n):
                flowlet_burst.append((src_ip, dst_ip, np.ceil(flow_size / self.break_to_message_n), curr_time, str(flow_id) + "." + str(count)))
                curr_time += self.inter_arrival_time()
                count = count + 1
            return flowlet_burst


class CDFFlowletGenerator(object):
    def __init__(self, cdf_generator, inter_arrival_time):
        """
        :param cdf_generator: CDFGenerator object for message size distribution
        :param inter_arrival_time: Function for interarrival time between messages
        """
        self.cdf_generator = cdf_generator
        self.inter_arrival_time = inter_arrival_time

    def generate_flowlet_from_flow(self, flow) -> list:
        message_burst = []
        src_ip, dst_ip, flow_size, time, flow_id = flow
        if flow_size <= Utils.mtu_size():
            return [(src_ip, dst_ip, flow_size, time, str(flow_id) + "." + "0")], time  # Do not allocate new time!
        count = 0
        while flow_size > 0:
            message_size = min(flow_size, self.cdf_generator.get_sample())
            curr_time = time
            data = (src_ip, dst_ip, message_size, curr_time, str(flow_id) + "." + str(count))
            message_burst.append(data)
            count = count + 1
            flow_size = flow_size - message_size
            curr_time += self.inter_arrival_time()

        return message_burst, curr_time
