import ipaddress
import numpy as np

class FlowGenerator(object):
    def __init__(self, policy_size, cdf_generator, inter_arrival_time, mtu_size=1500):
        self.cdf_generator = cdf_generator
        self.inter_arrival_time = inter_arrival_time
        self.policy_size = policy_size
        self.mtu_size = mtu_size
        self.flow_id = 0
        self.clock = 0

    def generate_flow(self):
        src_ip, dst_ip = '192.168.1.1', np.random.randint(self.policy_size)
        next_flow_time = self.clock + self.inter_arrival_time()
        data = (src_ip, dst_ip, np.ceil(self.cdf_generator.get_sample() / self.mtu_size), next_flow_time, self.flow_id)
        self.clock = next_flow_time
        self.flow_id = self.flow_id + 1
        return data
