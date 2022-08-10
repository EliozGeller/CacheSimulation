import json
import threading
import time
import sys
sys.path.append('../')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
import pandas as pd
from Policy import Policy
from TrafficGenerator.ApplicationGenerator import OnlineApplicationGenerator, ApplicationGenerator, \
    FlowFileApplicationGenerator
from TrafficGenerator.CDFGenerator import CDFGenerator
from TrafficGenerator.FlowGenerator import FlowGenerator
from TrafficGenerator.FlowletGenerator import ThresholdFlowletGenerator
from TrafficGenerator.PacketScheduler import PacketScheduler
from TimeSeriesLogger import *
import seaborn as sns
from collections import OrderedDict
from PlotTrace import PlotTG
import itertools





class TestUtils(object):
    @staticmethod
    def variable_distribution_size():
        return '../data/traffic/FBHadoop/msgSizeDist_AllLoc_Facebook_Hadoop.csv'

    @staticmethod
    def aggregate_output_per_flow_id(data_array):
        flows = {}
        for data in data_array:
            src, dst, size, time, flow_id = data
            flows[flow_id] = size if flows.get(flow_id) is None else flows[flow_id] + size
        return flows

    @staticmethod
    def get_flow_array(n_flows):
        p = TestUtils.get_policy()
        cdf_generator = CDFGenerator(TestUtils.variable_distribution_size())
        flow_generator = FlowGenerator(p, cdf_generator, TestUtils.inter_arrival_time)
        flow_array = []
        for i in range(n_flows):
            flow_array.append(flow_generator.generate_flow())  # only for testing size - not time

        return flow_array

    @staticmethod
    def plot_message_array(message_array, x_label, y_label, title):
        flow_to_size = TestUtils.aggregate_output_per_flow_id(message_array)
        x_data = range(len(list(flow_to_size.values())))
        y_data = np.sort(list(flow_to_size.values()))
        PlotTG.plot_xy(x_data, y_data, x_label, y_label, title)
        PlotTG.plot_cdf(y_data, x_label, title + "CDF - Pr(sample <= size)")

    @staticmethod
    def get_policy():
        return Policy('https://www.cidr-report.org/cgi-bin/as-report?as=AS16509&view=2.0',
                      '../data/AS16509.json')

    @staticmethod
    def get_flow_array_json_path(idx=""):
        return "flow_array.json" + idx

    @staticmethod
    def get_message_array_json_path(idx=""):
        return "message_array.json" + idx

    @staticmethod
    def inter_arrival_time():
        return np.random.exponential(1)

    @staticmethod
    def calculate_pdf_of_packets_from_cdf_file(cdf_distribution_file_path):
        df = pd.read_csv(cdf_distribution_file_path, header=[0])
        size_header, cdf_header = df.columns
        pdf_value = []
        prev_cdf = 0
        for cdf_value in df[cdf_header]:
            pdf_value.append(cdf_value - prev_cdf)
            prev_cdf = cdf_value
        df['pdf_value'] = pdf_value

        mtu = 1500
        packet_prob_histogram = {}
        for size, pdf_value in zip(df[size_header], df['pdf_value']):
            if packet_prob_histogram.get(np.ceil(size / mtu)) is None:
                packet_prob_histogram[int(np.ceil(size / mtu))] = pdf_value
            else:
                packet_prob_histogram[int(np.ceil(size / mtu))] = packet_prob_histogram[int(np.ceil(size / mtu))
                                                                  ] + pdf_value

        return packet_prob_histogram

    @staticmethod
    def calculate_pdf_of_flows_from_flow_array(flow_array):
        flow_size_idx = 2
        flow_size_histogram = {}
        for flow in flow_array:
            size = int(flow[flow_size_idx])
            if flow_size_histogram.get(size):
                flow_size_histogram[size] += 1
            else:
                flow_size_histogram[size] = 1

        for key, value in flow_size_histogram.items():
            flow_size_histogram[key] = value / len(flow_array)

        return flow_size_histogram

    @staticmethod
    def claculate_pdf_packet_from_flow_size(flow_array, packet_array):
        flow_size_idx = 2
        flow_id_idx = 4
        flow_to_size = OrderedDict()
        for flow in flow_array:
            flow_to_size[int(flow[flow_id_idx])] = int(flow[flow_size_idx])

        packet_size_hist = {}
        for packet in packet_array:
            flow_id = int(packet[flow_id_idx].split(".")[0])
            flow_original_size = flow_to_size[flow_id]
            if flow_original_size in packet_size_hist:
                packet_size_hist[flow_original_size] += 1
            else:
                packet_size_hist[flow_original_size] = 1

        sum_value = sum(packet_size_hist.values())
        for key, value in packet_size_hist.items():
            packet_size_hist[key] = value / sum_value

        return packet_size_hist

    @staticmethod
    def replace_index_dic(input_dict):
        idx = np.array(input_dict.keys())
        vals = np.array(input_dict.values())

        x_dim = max([x[0] for x in input_dict.keys()])
        y_dim = max([y[1] for y in input_dict.keys()])

        out = np.zeros((y_dim, x_dim))  # , dtype=vals.dtype) # transpose

        for tup in input_dict.keys():
            i, j = tup
            out[j - 1][i - 1] = input_dict[(i, j)]  # Assigning as transpose

        return out

    @staticmethod
    def calulcate_line_utilization_over_time(packet_array, flow_array):
        flow_size_idx = 2
        flow_time_idx = 3
        flow_id_idx = 4
        packet_time_hist = {}
        flow_size_count_over_time = {}
        flow_id_to_size = {int(flow[flow_id_idx]): int(flow[flow_size_idx]) for flow in flow_array}
        all_sizes = np.unique(list(flow_id_to_size.values()))
        size_to_idx = {all_sizes[i]: i for i in range(len(all_sizes))}
        curr_time = 0
        for packet in packet_array:
            if packet[flow_time_idx] > curr_time:
                curr_time = curr_time + 1
                packet_time_hist[curr_time] = 1
                flow_id = int(packet[flow_id_idx].split('.')[0])
                flow_size_idx = size_to_idx[flow_id_to_size[flow_id]]
                flow_size_count_over_time[(curr_time, flow_size_idx)] = 1
            else:
                packet_time_hist[curr_time] += 1
                flow_id = int(packet[flow_id_idx].split('.')[0])
                flow_size_idx = size_to_idx[flow_id_to_size[flow_id]]
                two_d_idx = (curr_time, flow_size_idx)
                if flow_size_count_over_time.get(two_d_idx):
                    flow_size_count_over_time[two_d_idx] += 1
                else:
                    flow_size_count_over_time[two_d_idx] = 1

        # flow_size_count_2d = TestUtils.replace_index_dic(flow_size_count_over_time)
        flow_size_count_2d = []

        return packet_time_hist, flow_size_count_2d, size_to_idx


class TestBase(object):

    @staticmethod
    def test_cdf_generator():
        from_path_cdf_generator = CDFGenerator(TestUtils.variable_distribution_size())
        random_sample_cdf_generator = CDFGenerator()
        n_samples = 10000
        from_path_cdf_gen_samples = [from_path_cdf_generator.get_sample() for i in range(n_samples)]
        # PlotTG.plot_xy([i for i in range(n_samples)], path_cdf_gen_samples, "sample id", "sample value", "Path CDF")
        PlotTG.plot_cdf(from_path_cdf_gen_samples, "sample size", "Path CDF - Pr(sample <= size)",
                        TestUtils.variable_distribution_size())
        plt.show()

    @staticmethod
    def test_flow_message_generator():
        cdf_generator = CDFGenerator(TestUtils.variable_distribution_size())
        message_inter_arrival_time = lambda: np.random.exponential(1 / 500)  # 10 flows in time unit
        n_flows = 5000
        threshold = cdf_generator.get_size_by_probability(0.6)
        break_message_count = 10
        message_generator = ThresholdFlowletGenerator(message_inter_arrival_time, threshold, break_message_count)

        p = TestUtils.get_policy()
        cdf_generator = CDFGenerator(TestUtils.variable_distribution_size())
        flow_generator = FlowGenerator(p, cdf_generator, lambda: np.random.exponential(1 / 100))
        flow_array = []
        for i in range(n_flows):
            flow_array.append(flow_generator.generate_flow())  # only for testing size - not time

        messages = []
        for flow in flow_array:
            print(flow)
            msg = message_generator.generate_flowlet_from_flow(flow)
            messages = messages + msg

    @staticmethod
    def test_application_generator_and_packet_scheduler():
        n_flows = 500000  # 5000 flows ~ 10 sec
        flow_distribution_path = TestUtils.variable_distribution_size()
        flowlet_break_p = 1
        flowlet_break_count = 10
        policy = TestUtils.get_policy()
        flow_per_sec = 500
        flowlet_per_sec = 500
        flow_inter_arrival_time = lambda: np.random.exponential(1 / flow_per_sec)
        flowlet_inter_arrival_time = lambda: np.random.exponential(1 / flowlet_per_sec)

        online_app_gen = OnlineApplicationGenerator(n_flows, flow_distribution_path, flowlet_break_p,
                                                    flowlet_break_count, policy, flow_inter_arrival_time,
                                                    flowlet_inter_arrival_time,
                                                    time_limit=100,
                                                    path_save_flow_array='flow_trace_50000.json',
                                                    path_save_flowlet_array='flowlet_trace_50000.json')

        # Line rate 1 Gb/sec ~ 100k pps
        # 100k pps 1/100k sec between packets
        packet_scheduler = PacketScheduler(online_app_gen, lambda: 1 / 100000)

        t0 = time.time()
        online_app_gen.generate()
        print(str(time.time() - t0))

        t0 = time.time()
        packet_scheduler.generate_packets()
        packet_array = []
        count = 0
        while not packet_scheduler.done or bool(packet_scheduler.packet_queue):
            packet = packet_scheduler.pop_packet()
            if packet:
                packet_array.append(packet)
                count = count + 1
                if count % 10000 == 0:
                    print(count)
                    print(packet[3])
        print(str(time.time() - t0))
        ApplicationGenerator.data_list_to_json(packet_array, 'packet_trace.json')


    @staticmethod
    def plot_and_analyze_json_files():
        with open('flow_trace4.json') as f:
            flow_array = json.load(f)

        with open('flowlet_trace4.json') as f:
            flowlet_array = json.load(f)

        with open('packet_trace4.json') as f:
            packet_array = json.load(f)

        # print(len(packet_array))
        # # Plot 1 - flows sorted by size
        # flow_size_idx = 2
        # flow_time_idx = 3
        # flow_id_idx = 4
        # print(len(flow_array))

        # tg_data = TestUtils.calculate_pdf_of_flows_from_flow_array(flow_array)
        # file_data = TestUtils.calculate_pdf_of_packets_from_cdf_file(TestUtils.variable_distribution_size())
        #
        # diff_dict = {}
        # for size in sorted(list(tg_data.keys())):
        #     print("size: " + str(size))
        #     print("tg_data["+str(size)+"] = " + str(tg_data[size]))
        #     print("file_data["+str(size)+"] = " + str(file_data[size]))
        #     diff_dict[size] = tg_data[size] - file_data[size]
        #
        # print("end")
        #
        # cdf_n_digit_after_the_dot = 5
        # x_data = [list(file_data.keys()), list(tg_data.keys())]
        # y_data = [list(file_data.values()), list(tg_data.values())]
        # # #
        # PlotTG.plot_multiple_scatters(x_data, y_data, "Flow Size", "Probability (PDF)",
        #                               "File PDF vs Traffic Generator PDF (packet level)", ["File PDF", "TG PDF"], scale='log')
        #
        # # # Plot 2 - flows CDF vs CDF File
        # PlotTG.plot_cdf([flow[flow_size_idx] for flow in flow_array],
        #                 "sample size", "Path CDF - Pr(sample <= size)", TestUtils.variable_distribution_size())
        # # # Plot 3 - Main plot
        # PlotTG.main_plot(flow_array, flowlet_array)
        #
        # # # Plot 4 - Packet from size PDF
        # packet_from_size_pdf = TestUtils.claculate_pdf_packet_from_flow_size(flow_array, packet_array)
        # PlotTG.plot_multiple_scatters([packet_from_size_pdf.keys()], [packet_from_size_pdf.values()], "Flow Size",
        #                               "Probability (PDF)", "Probability For Receiving Packet From Flow Size (PDF)", [''], scale='linear')
        #
        # packet_from_size_cdf = {}
        # curr_cdf = 0
        # for size in sorted(list(packet_from_size_pdf.keys())):
        #     packet_from_size_cdf[size] = curr_cdf + packet_from_size_pdf[size]
        #     curr_cdf = packet_from_size_cdf[size]
        #
        # PlotTG.plot_multiple_scatters([packet_from_size_cdf.keys()], [packet_from_size_cdf.values()], "Flow Size",
        #                               "Probability (CDF)", "Probability For Receiving Packet From Flow Size (CDF)", [''], scale='linear')
        #
        # Plot 4 - Unique Flow Count Extracted From Packets
        flow_extract_from_packet = [int(packet[4].split(".")[0]) for packet in packet_array]
        i = 0
        step = 10000
        conseq_data = {}
        while i + step < len(flow_extract_from_packet):
            conseq_data[(i, i + step)] = len((np.unique(flow_extract_from_packet[int(i):int(i + step)])))
            i += step / 2

        PlotTG.plot_xy([x[0] for x in list(conseq_data.keys())], conseq_data.values(), "Packet Window (10k packets in a window)",
                       'Unique Flow Count', 'Unique Flow Count Extracted From Packets')

        # Plot 5 - Line Utilization
        packet_time_hist, flow_size_count_2d, size_to_idx = TestUtils.calulcate_line_utilization_over_time(packet_array,
                                                                                                           flow_array)
        PlotTG.plot_xy(packet_time_hist.keys(), packet_time_hist.values(), "Arrival Time",
                       'Packet Count In Time Interval', 'Line Utilization Over Time')

        # Plot 6 - Plot Heatmap time over flow size
        normalized_flow_size_count_2d = flow_size_count_2d / np.sum(flow_size_count_2d, axis=0)
        fig, ax = plt.subplots()
        flow_sizes = [int(i) for i in list(size_to_idx.keys())]
        ytick = []
        curr_numeric_ytick = flow_sizes[0]
        for size, i in zip(flow_sizes, range(len(flow_sizes))):
            if i % 4 == 0:
                ytick.append(size)
                print("size = " + str(size))
                print("curr_numeric_ytick = " + str(curr_numeric_ytick))
            else:
                ytick.append('')

        sns.heatmap(normalized_flow_size_count_2d, yticklabels=ytick, cmap="YlOrBr")
        ax.set_xlabel("Time")

        # Flowlets generated by time
        # flowlet_time_to_size = {x[3] : x[2] for x in sorted(list(itertools.chain.from_iterable(flowlet_array.values())), key=lambda x: x[3])}
        # acc_flowlet_time_to_size = {}
        # acc_time = 0
        # acc_packets = 0
        # for time in sorted(list(flowlet_time_to_size.keys())):
        #     acc_flowlet_time_to_size[time] = acc_packets + flowlet_time_to_size[time]
        #     acc_packets = acc_flowlet_time_to_size[time]
        #
        # packet_rate = 1 / 100000
        # last_packet_time = -1
        # idle_time = []
        # for flowlet_time in flowlet_time_to_size.keys():
        #     fastest_sent_time = flowlet_time + packet_rate*flowlet_time_to_size[flowlet_time]
        #     next_available_time = max(last_packet_time, fastest_sent_time)
        #     if fastest_sent_time > last_packet_time:
        #         print(flowlet_time)
        #         print(flowlet_time - last_packet_time)
        #         print("")
        #         idle_time.append(flowlet_time)
        #     last_packet_time = next_available_time
        #
        # print(len(idle_time))

        plt.show()

def main():
    # TestBase.test_cdf_generator()
    # TestBase.test_flow_message_generator()
    # TestBase.test_application_generator_and_packet_scheduler()
    TestBase.plot_and_analyze_json_files()
    pass


if __name__ == "__main__":
    main()
