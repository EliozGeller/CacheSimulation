import abc
import json
from TrafficGenerator.CDFGenerator import CDFGenerator
from TrafficGenerator.FlowGenerator import FlowGenerator
from TrafficGenerator.FlowletGenerator import ThresholdFlowletGenerator
import ipaddress
import threading

message_size_idx, flow_size_idx = 2, 2


class ApplicationGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        self.clock = 0
        self.n_queues = 16
        self.flowlet_queue = {i: [] for i in range(self.n_queues)}

    @abc.abstractmethod
    def generate(self) -> list:
        raise NotImplementedError

    @staticmethod
    def data_list_from_json(data_json_path):
        with open(data_json_path) as f:
            jsonified_array = json.load(f)
        data_array = []
        for jsonified_data in jsonified_array:
            flow = (ipaddress.ip_address(jsonified_data[0]), ipaddress.ip_address(jsonified_data[1])) + \
                   tuple(jsonified_data[2:])
            data_array.append(flow)

        return data_array

    @staticmethod
    def data_list_to_json(data_array, data_json_path):
        out_data_array = []
        for data in data_array:
            flow = (str(data[0]), str(data[1])) + \
                   tuple(data[2:])
            out_data_array.append(flow)
        print("start json dump")
        with open(data_json_path, 'w+') as f:
            json.dump(out_data_array, f)
        print("end json dump")

    @staticmethod
    def data_dict_to_json(data_dict, data_json_path):
        out_data_dict = {}
        for key in data_dict:
            jsonified_array = []
            for data in data_dict[key]:
                flow = (str(data[0]), str(data[1])) + \
                       tuple(data[2:])
                jsonified_array.append(flow)
            out_data_dict[key] = jsonified_array

        with open(data_json_path, 'w+') as f:
            json.dump(out_data_dict, f)

    @staticmethod
    def data_dict_from_json(data_json_path):
        with open(data_json_path) as f:
            jsonified_dict = json.load(f)
        data_dict = {}
        for key in jsonified_dict:
            data_array = []
            for jsonified_data in jsonified_dict[key]:
                flow = (ipaddress.ip_address(jsonified_data[0]), ipaddress.ip_address(jsonified_data[1])) + \
                       tuple(jsonified_data[2:])
                data_array.append(flow)
            data_dict[key] = data_array

        return data_array


class OnlineApplicationGenerator(ApplicationGenerator):
    def __init__(self, n_flows, flow_distribution_path, flowlet_break_count, policy_size,
                 flow_inter_arrival_time, flowlet_inter_arrival_time, time_limit=None, size_limit=None,
                 path_save_flow_array=None, path_save_flowlet_array=None, flow_distribution_pdf=None):
        ApplicationGenerator.__init__(self)
        flow_cdf_generator = CDFGenerator(flow_distribution_path, flow_distribution_pdf)
        self.flow_generator = FlowGenerator(policy_size, flow_cdf_generator, flow_inter_arrival_time)
        self.flowlet_generator = ThresholdFlowletGenerator(flowlet_inter_arrival_time,
                                                           flowlet_break_count)
        self.path_save_flowlet_queue = path_save_flowlet_array
        self.path_save_flow_array = path_save_flow_array
        self.flows_to_process = n_flows
        self.flow_array = None if path_save_flow_array is None else []
        self.time_limit = time_limit
        self.size_limit = size_limit
        self.done = False

    def generate(self):
        total_packets = 0
        size_index = 2
        self.done = False
        for i in range(self.flows_to_process):
            flow = self.flow_generator.generate_flow()
            flow_id = flow[-1]
            total_packets += flow[size_index]

            if self.path_save_flow_array:
                self.flow_array.append(flow)

            if (self.time_limit and self.flow_generator.clock >= self.time_limit) or (
                    self.size_limit and total_packets >= self.size_limit_limit):
                self.done = True
                break

            flowlet_array = self.flowlet_generator.generate_flowlet_from_flow(flow)
            self.flowlet_queue[flow_id % self.n_queues] = self.flowlet_queue[flow_id % self.n_queues] + flowlet_array

        self.sort_flowlet_queue_by_time()
        self.done = True
        self.clean_empty_queues()
        self.save_trace()
        return total_packets, self.flow_generator.clock

    def sort_flowlet_queue_by_time(self):
        time_idx = 3
        for key in self.flowlet_queue:
            self.flowlet_queue[key].sort(key=lambda x: float(x[time_idx]))

    def save_trace(self):
        if self.path_save_flowlet_queue:
            ApplicationGenerator.data_dict_to_json(self.flowlet_queue, self.path_save_flowlet_queue)
        if self.path_save_flow_array:
            ApplicationGenerator.data_list_to_json(self.flow_array, self.path_save_flow_array)

    def clean_empty_queues(self):
        for i in range(self.n_queues):
            if not bool(self.flowlet_queue[i]):
                del self.flowlet_queue[i]
        self.n_queues = len(list(self.flowlet_queue.keys()))
