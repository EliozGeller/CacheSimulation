from TrafficGenerator.ApplicationGenerator import ApplicationGenerator
flow_size_idx = 2
flow_time_idx = 3
flow_id_idx = 4

class PacketScheduler:
    def __init__(self, application_generator, inter_arrival_time, path_save_packet_array='packet_trace.json',
                 deficit_param=16, time_limit=None):  # implementing round-robin, supporting WDRR
        self.application_generator = application_generator
        self.deficit_param = deficit_param
        self.path_save_packet_array = path_save_packet_array
        self.clock = 0
        self.inter_arrival_time = inter_arrival_time
        self.done = False
        self.packet_queue = []
        self.time_limit = time_limit

    def generate_packets(self):
        self.done = False
        empty_queue_idx = []
        flows_to_delete = 0
        while not self.application_generator.done or bool(self.application_generator.flowlet_queue):
            # case 2: All packets timestamp are > self.clock - increase time by the minimal value
            self.clock = max(self.clock,
                             min(float(q[0][flow_time_idx]) for q in self.application_generator.flowlet_queue.values()))
            if self.time_limit and self.clock >= self.time_limit:
                print("Reached time limit: {0}".format(self.time_limit))
                break
            # iterate over all head of the flowlets in the queue
            for flowlet_queue in self.application_generator.flowlet_queue.values():  # {flow_id : flowlet_queue}
                flowlet = flowlet_queue[0]
                # case 1: there is a packet with timestamp <= self.clock
                if float(flowlet[flow_time_idx]) <= self.clock:
                    # case 1.1: flowlet > self.deficit_param
                    if flowlet[flow_size_idx] > self.deficit_param:
                        src_ip, dst_ip, packet_size, time, id = flowlet
                        self.generate_packets_from_flowlet((src_ip, dst_ip, self.deficit_param, time, id))
                        flowlet_queue[0] = (src_ip, dst_ip, packet_size - self.deficit_param, self.clock, id)
                        for i in range(1, len(flowlet_queue)):
                            if float(flowlet_queue[i][flow_time_idx]) >= self.clock:
                                break
                            flowlet_queue[i] = flowlet_queue[i][:flow_size_idx + 1] + (self.clock,) + flowlet_queue[i][flow_id_idx:]
                    # case 1.2: flowlet <= self.deficit_param
                    else:
                        self.generate_packets_from_flowlet(flowlet)
                        flowlet_queue.pop(0)
                        if not flowlet_queue:  # empty queue
                            flow_id_hash = int(flowlet[flow_id_idx].split(".")[0]) % self.application_generator.n_queues
                            empty_queue_idx.append(flow_id_hash)

            for flow_idx in empty_queue_idx:
                del self.application_generator.flowlet_queue[flow_idx]
            empty_queue_idx = []

        ApplicationGenerator.data_list_to_json(self.packet_queue, self.path_save_packet_array)
        self.done = True

    def generate_packets_from_flowlet(self, flowlet):
        count = 0
        src_ip, dst_ip, flowlet_packets_count, time, flowlet_id = flowlet
        self.clock = max(self.clock, time)  # avoid cases that the next free time to transmit < flowlet arrival time
        while flowlet_packets_count > 0:
            packet_size = 1
            self.packet_queue.append((src_ip, dst_ip, packet_size, self.clock, str(flowlet_id) + "." +
                                      str(count)))
            flowlet_packets_count = flowlet_packets_count - packet_size
            self.clock += self.inter_arrival_time()
            count = count + 1

    def pop_packet(self):
        value = self.packet_queue.pop(0) if bool(self.packet_queue) else None
        return value
