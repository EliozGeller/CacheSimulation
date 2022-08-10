import threading

from TrafficGenerator.PacketScheduler import PacketScheduler
from TrafficGenerator.ApplicationGenerator import OnlineApplicationGenerator, FlowFileApplicationGenerator, \
    MessageFileApplicationGenerator
import numpy as np



class TrafficGenerator(object):
    def __init__(self, configuration_array, policy):
        self.policy = policy
        self.application_generators = [self.build_application_generator(config) for config in configuration_array]
        self.packet_scheduler = PacketScheduler(self.application_generators)
        self.end = False

    def build_application_generator(self, data):
        # (MessageGeneator, message_json_path)
        if "message" in data[0].lower():
            json_path = data[1]
            return MessageFileApplicationGenerator(json_path)

        # (FlowGenerator, flow_json_path, message_cdf_path, exp_value, path_to_save_message_array)
        if "flow" in data[0].lower():
            application_generator_type, flow_json_path, message_cdf_path, exp_value, path_to_save_message_array = data
            return FlowFileApplicationGenerator(flow_json_path, message_cdf_path,
                                                lambda: np.random.exponential(float(exp_value)), path_to_save_message_array)

        # (OnlineGenerator, n_flows, flow_cdf_path, message_cdf_path, flow_exp_value, message_exp_value,
        #   path_to_save_flow_array, path_to_save_message_array)
        if "online" in data[0].lower():
            application_generator_type, n_flows, flow_cdf_path, message_cdf_path,  flow_exp_value, \
                message_exp_value, path_to_save_flow_array, path_to_save_message_array = data
            return OnlineApplicationGenerator(n_flows, flow_cdf_path, message_cdf_path, self.policy,
                                              lambda: np.random.exponential(float(flow_exp_value)),
                                              lambda: np.random.exponential(float(message_exp_value)),
                                              path_to_save_flow_array,
                                              path_to_save_message_array)

    def generate(self):
        self.end = False
        packet_injector_array = []
        for application_generator in self.application_generators:
            packet_injector_array.append(threading.Thread(target=application_generator.generate_packets))

        for packet_injector in packet_injector_array:
            packet_injector.start()

        packet_scheduler = threading.Thread(target=self.packet_scheduler.push_packet)
        packet_scheduler.start()

        for packet_injector in packet_injector_array:
            packet_injector.join()

        packet_scheduler.join()
        self.end = True

    def get_packet(self):
        return self.packet_scheduler.pop_packet()
