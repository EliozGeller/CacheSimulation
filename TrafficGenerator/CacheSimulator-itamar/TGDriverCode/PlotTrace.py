import os
import sys

sys.path.append('../')
import json
from collections import OrderedDict
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import colorsys

import matplotlib as mpl
mpl.rcParams['agg.path.chunksize'] = 10000

# constants
packet_dst_idx = 1
flow_size_idx = 2
flow_time_idx = 3
flow_id_idx = 4
xy_label_font_size = 48
title_font_size = 48
xy_tick_font_size = 36

# globals

plot_list = [
    # 'file_pdf_vs_traffic_generator_pdf',
    # 'file_cdf_vs_traffic_generator_cdf',
    # 'packet_from_size_pdf_cdf',
    # 'flow_id_bar_size',
    'line_utilization',
    # 'heatmap_time_over_flow_size',
    'unique_flow_count',
    # 'plot_flow_duration_cdf',
    # 'plot_flow_duration_over_time',
    # 'plot_unique_and_overlap_rules',
    # 'plot_flow_duration_by_percent_bucketing',
    'plot_trace_burstiness'
    ]

figs_to_save = {}


class PlotTG(object):
    @staticmethod
    def get_colors(num_colors):
        colors = []
        for i in np.arange(0., 360., 360. / num_colors):
            hue = i / 360.
            lightness = (50 + np.random.rand() * 10) / 100.
            saturation = (90 + np.random.rand() * 10) / 100.
            colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))
        return colors

    @staticmethod
    def plot_xy(x_data, y_data, x_label, y_label, title):
        fig, ax = plt.subplots()
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.plot(x_data, y_data)
        ax.set_xlabel(x_label, fontsize=xy_label_font_size)
        ax.set_ylabel(y_label, fontsize=xy_label_font_size)
        ax.set_title(title, fontsize=title_font_size)
        ax.tick_params(labelsize=xy_tick_font_size)
        return fig

    @staticmethod
    def plot_cdf(data, data_x="data", data_title="", reference_data_path=None):
        x = np.linspace(min(data), max(data), 101)
        count_dict = {i: 0 for i in x}
        for i in x:
            for j in data:
                if j < i:
                    count_dict[i] += 1
        max_n = max(count_dict.values())
        if reference_data_path:
            df = pd.read_csv(reference_data_path, header=[0])

        fig = plt.figure()
        ax1 = fig.add_subplot(111, label="1")
        if reference_data_path:
            ax2 = fig.add_subplot(111, label="2", frame_on=False)

        ax1.plot(count_dict.keys(), [i / max_n for i in count_dict.values()], color="C0")
        ax1.set_xlabel("CDF Generator Sample Size", color="C0")
        ax1.set_ylabel("CDF Generator Sample Size Probability", color="C0")
        ax1.tick_params(axis='x', colors="C0")
        ax1.tick_params(axis='y', colors="C0")

        if reference_data_path:
            # df headers: size, prob. extracting the value from df
            ax2.plot([i for i in df[df.columns[0]]], [i for i in df[df.columns[1]]], color="C1")
            ax2.xaxis.tick_top()
            ax2.yaxis.tick_right()
            ax2.set_xlabel('CDF File Sample Size', color="C1")
            ax2.set_ylabel('CDF File Sample Size Probability', color="C1")
            ax2.xaxis.set_label_position('top')
            ax2.yaxis.set_label_position('right')
            ax2.tick_params(axis='x', colors="C1")
            ax2.tick_params(axis='y', colors="C1")

        return fig
        # plt.tight_layout()
        # fig.show()

    @staticmethod
    def plot_multiple_lines(x_data_array, y_data_array, x_label, y_label, title, line_description_array):
        fig, ax = plt.subplots()
        for x_data, y_data, line_descp in zip(x_data_array, y_data_array, line_description_array):
            ax.plot(x_data, y_data, label=line_descp)
        ax.legend(loc='upper right', prop={'size': 24})
        ax.set_xlabel(x_label, fontsize=xy_label_font_size)
        ax.set_ylabel(y_label, fontsize=xy_label_font_size)
        ax.set_title(title, fontsize=title_font_size)
        ax.tick_params(labelsize=xy_tick_font_size)
        # ax.set_yscale('log')
        return fig

    @staticmethod
    def plot_multiple_scatters(x_data_array, y_data_array, x_label, y_label, title, line_description_array,
                               scale='linear'):
        fig, ax = plt.subplots()
        for x_data, y_data, line_descp in zip(x_data_array, y_data_array, line_description_array):
            ax.scatter(x_data, y_data, label=line_descp)

        ax.set_yscale(scale)
        ax.set_xscale('linear')
        ax.set_xlabel(x_label, fontsize=xy_label_font_size)
        ax.set_ylabel(y_label, fontsize=xy_label_font_size)
        ax.set_title(title, fontsize=title_font_size)
        ax.tick_params(labelsize=xy_tick_font_size)
        ax.legend()
        ax.grid(True)

        return fig

    @staticmethod
    def flow_size_color(flow_array, flowlet_dict):
        # Plot 3 - Flow arrival time, Flow size bar chart, Flowlet arrival time
        # # Two plots
        # # Flow size over time
        # # Scatter MSGs over time
        size_scale = 100
        x1 = [x[3] for x in flow_array]
        y1 = [y[4] for y in flow_array]
        s = [s[2] / size_scale for s in flow_array]

        size_idx = 2
        color_by_size = sns.color_palette("coolwarm", n_colors=int(1 + max([x[size_idx] for x in flow_array])))
        flow_colors = [color_by_size[int(flow[size_idx])] for flow in flow_array]

        size_hist = {}
        for flow in flow_array:
            flow_size = flow[size_idx]
            if flow_size in size_hist:
                size_hist[flow_size] += 1
            else:
                size_hist[flow_size] = 1

        flowlet_array = []
        for flow_flowlets in flowlet_dict.values():
            flowlet_array = flowlet_array + flow_flowlets

        flowlet_colors = [flow_colors[int(flowlet[-1].split(".")[0])] for flowlet in flowlet_array]

        time_idx = 3
        x3 = [x[time_idx] for x in flowlet_array]
        y3 = [0 for y in flowlet_array]
        s3 = [s[2] / size_scale for s in flowlet_array]

        # extract flow id from the msg

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
        fig.suptitle('Flow Generator Arrival Time And Packet Count')

        ax1.set_xlabel("Arrival Time")
        ax1.set_ylabel("Flow ID")
        ax1.scatter(x1, y1, s=s, c=flow_colors)

        ax2.set_title("Flow Size By ID")
        ax2.bar([tup[4] for tup in flow_array], [size[size_idx] for size in flow_array], 1)
        for i in range(len(flow_array)):
            ax2.get_children()[i].set_color(flow_colors[i])
        ax2.set_xlabel("Flow ID")
        ax2.set_ylabel("Packet count")

        ax3.set_xlabel("Message Arrival Time")
        ax3.set_ylabel("Flow ID (Extracted from message)")
        ax3.scatter(x3, y3, s=s3, c=flowlet_colors)

        fig.tight_layout()

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
    def calulcate_line_utilization_over_time(packet_array, time_interval=0.1, line_rate=100000):
        # Assuming that packet array is sorted by arrival time
        # Rate is 100k packets/sec
        packet_time_hist = {}
        start_interval = 0
        end_interval = time_interval
        effective_line_rate = line_rate * time_interval
        for packet in packet_array:
            if float(packet[flow_time_idx]) > start_interval and float(packet[flow_time_idx]) <= end_interval:
                if packet_time_hist.get(start_interval):
                    packet_time_hist[start_interval] += 1
                else:
                    packet_time_hist[start_interval] = 1
            else:
                # Advance the time interval if the packet time is either large from the end interval
                while float(packet[flow_time_idx]) > end_interval:
                    start_interval = end_interval
                    end_interval = end_interval + time_interval
                if packet_time_hist.get(start_interval):
                    packet_time_hist[start_interval] += 1
                else:
                    packet_time_hist[start_interval] = 1
        return packet_time_hist

    @staticmethod
    def replace_index_dic(input_dict):
        N_cols = max([x[0] for x in input_dict.keys()])
        N_rows = max([y[1] for y in input_dict.keys()])

        df = pd.DataFrame(np.zeros((N_rows, N_cols)))

        for tup in input_dict.keys():
            i, j = tup

            df[i - 1][j - 1] = input_dict[(i, j)]

        return df

    @staticmethod
    # Packets in time interval
    def calulcate_heatmap_data(packet_array, flow_array, time_interval=0.1):
        # Build log scale of flow sizes
        max_flow_size = max([flow[flow_id_idx] for flow in flow_array])
        y_ticks = [2 ** i for i in range(int(1 + np.ceil(np.log2(max_flow_size))))]
        flow_size_count_over_time = {}
        # flow id to log scale of flow size (rounded to the closest power)
        flow_id_to_size = {int(flow[flow_id_idx]): int(np.rint(np.log2(flow[flow_size_idx]))) for flow in flow_array}
        all_sizes = np.unique(list(flow_id_to_size.values()))
        size_to_idx = {all_sizes[i]: i for i in range(len(all_sizes))}

        curr_time = 0
        curr_time_idx = 0
        for packet in packet_array:  # packet array is sorted by time
            if packet[flow_time_idx] > curr_time:  # open new time interval
                curr_time = curr_time + time_interval
                curr_time_idx = curr_time_idx + 1
                flow_id = int(packet[flow_id_idx].split('.')[0])
                heatmap_size_idx = size_to_idx[flow_id_to_size[flow_id]]
                flow_size_count_over_time[(curr_time_idx, heatmap_size_idx)] = 1
            else:  # append to existing time interval
                flow_id = int(packet[flow_id_idx].split('.')[0])
                heatmap_size_idx = size_to_idx[flow_id_to_size[flow_id]]
                two_d_idx = (curr_time_idx, heatmap_size_idx)
                if flow_size_count_over_time.get(two_d_idx):
                    flow_size_count_over_time[two_d_idx] += 1
                else:
                    flow_size_count_over_time[two_d_idx] = 1

        flow_size_count_2d = PlotTG.replace_index_dic(flow_size_count_over_time)

        return flow_size_count_2d, size_to_idx

    @staticmethod
    def calculate_unique_flow_count_data(packet_array, time_interval=0.1):
        unique_flow_count = {}
        flow_count_interval = []
        curr_time = 0
        curr_time_idx = 0
        for packet in packet_array:  # packet array is sorted by time
            if packet[flow_time_idx] > curr_time:  # open new time interval
                curr_time = curr_time + time_interval
                curr_time_idx = curr_time_idx + 1
                flow_count_interval = []
                flow_id = int(packet[flow_id_idx])#.split('.')[0])
                flow_count_interval.append(flow_id)
                unique_flow_count[curr_time] = 1

            else:  # append to existing time interval
                flow_id = int(packet[flow_id_idx])#.split('.')[0])
                if flow_id not in flow_count_interval:
                    flow_count_interval.append(flow_id)
                    if unique_flow_count.get(time_interval):
                        unique_flow_count[curr_time] += 1
                    else:
                        unique_flow_count[curr_time] = 1
        return unique_flow_count

    @staticmethod
    def calculate_unique_flow_count_data_per_bucket(packet_array, flow_to_bucket, buckets, time_interval=0.1):
        unique_flow_count = {}
        flow_count_interval = []
        curr_time = 0
        curr_time_idx = 0
        unique_flow_count_bucket = {key: {} for key in buckets}
        for packet in packet_array:  # packet array is sorted by time
            if packet[flow_time_idx] > curr_time:  # open new time interval
                curr_time = curr_time + time_interval
                curr_time_idx = curr_time_idx + 1
                flow_count_interval = []
                flow_id = int(packet[flow_id_idx].split('.')[0])
                flow_count_interval.append(flow_id)
                unique_flow_count[curr_time] = 1
                unique_flow_count_bucket[flow_to_bucket[flow_id]][curr_time] = 1

            else:  # append to existing time interval
                flow_id = int(packet[flow_id_idx].split('.')[0])
                if flow_id not in flow_count_interval:
                    flow_count_interval.append(flow_id)
                    if unique_flow_count.get(curr_time):
                        unique_flow_count[curr_time] += 1
                    else:
                        unique_flow_count[curr_time] = 1

                    if unique_flow_count_bucket[flow_to_bucket[flow_id]].get(curr_time):
                        unique_flow_count_bucket[flow_to_bucket[flow_id]][curr_time] += 1
                    else:
                        unique_flow_count_bucket[flow_to_bucket[flow_id]][curr_time] = 1

        return unique_flow_count, unique_flow_count_bucket

    @staticmethod
    def calculate_packet_per_flow(packet_array):
        time_idx = 3
        packet_per_flow = {}
        for packet in packet_array:
            flow_id = int(packet[-1].split(".")[0])  # y
            packet_time = packet[time_idx]
            if packet_per_flow.get(flow_id):
                packet_per_flow[flow_id].append(packet_time)
            else:
                packet_per_flow[flow_id] = [packet_time]
        return packet_per_flow


class PlotData:

    def __init__(self, flow_trace_path=None, flowlet_trace_path=None, packet_trace_path=None, json_path=None):
        if flow_trace_path:
            with open(flow_trace_path) as f:
                self.flow_array = json.load(f)
        else:
            self.flow_array = None

        if flowlet_trace_path:
            with open(flowlet_trace_path) as f:
                self.flowlet_array = json.load(f)
        else:
            self.flowlet_array = None

        if packet_trace_path:
            with open(packet_trace_path) as f:
                self.packet_array = json.load(f)
        else:
            self.packet_array = None

        if json_path:
            with open(json_path) as f:
                self.data_plot = json.load(f)
        else:
            self.data_plot = {}

    def to_json(self, path):
        with open(path, 'w') as f:
            json.dump(self.data_plot, f)

    # File PDF vs Traffic Generator PDF (packet level)
    def file_pdf_vs_traffic_generator_pdf(self):
        cdf_file_path = '../data/traffic/FBHadoop/msgSizeDist_AllLoc_Facebook_Hadoop.csv'
        tg_data = PlotTG.calculate_pdf_of_flows_from_flow_array(self.flow_array)
        file_data = PlotTG.calculate_pdf_of_packets_from_cdf_file(cdf_file_path)

        diff_dict = {}
        for size in sorted(list(tg_data.keys())):
            print("size: " + str(size))
            print("tg_data[" + str(size) + "] = " + str(tg_data[size]))
            print("file_data[" + str(size) + "] = " + str(file_data[size]))
            diff_dict[size] = tg_data[size] - file_data[size]

        print("end")
        x_data = [list(file_data.keys()), list(tg_data.keys())]
        y_data = [list(file_data.values()), list(tg_data.values())]

        self.data_plot["file_pdf_vs_traffic_generator_pdf"] = [x_data, y_data]

    def file_cdf_vs_traffic_generator_cdf(self):
        cdf_file_path = '../data/traffic/FBHadoop/msgSizeDist_AllLoc_Facebook_Hadoop.csv'
        self.data_plot["file_cdf_vs_traffic_generator_cdf"] = [[flow[flow_size_idx] for flow in self.flow_array],
                                                               cdf_file_path]

    # main plot
    def flow_id_bar_size(self):
        size_idx = 2
        color_by_size = sns.color_palette("coolwarm", n_colors=int(1 + max([x[size_idx] for x in self.flow_array])))
        flow_colors = [color_by_size[int(flow[size_idx])] for flow in self.flow_array]
        bar_data = ([tup[4] for tup in self.flow_array], [size[size_idx] for size in self.flow_array])
        self.data_plot["flow_id_bar_size"] = [color_by_size, flow_colors, bar_data]

    def packet_from_size_pdf_cdf(self):
        packet_from_size_pdf = PlotTG.claculate_pdf_packet_from_flow_size(self.flow_array, self.packet_array)

        packet_from_size_cdf = {}
        curr_cdf = 0
        for size in sorted(list(packet_from_size_pdf.keys())):
            packet_from_size_cdf[size] = curr_cdf + packet_from_size_pdf[size]
            curr_cdf = packet_from_size_cdf[size]

        self.data_plot["packet_from_size_pdf_cdf"] = [packet_from_size_pdf, packet_from_size_cdf]

    # Unique Flow Count Extracted From Packets
    def unique_flow_count(self, time_interval=0.1):
        # Plot 4 - Unique Flow Count Extracted From Packets
        conseq_data = PlotTG.calculate_unique_flow_count_data(self.packet_array, time_interval)
        self.data_plot['unique_flow_count'] = [conseq_data, time_interval]

    def line_utilization(self, time_interval=0.1, line_rate=100000):
        effective_line_rate = line_rate * time_interval
        packet_time_hist = PlotTG.calulcate_line_utilization_over_time(self.packet_array, time_interval)
        y_data = [100 * (value / effective_line_rate) for value in packet_time_hist.values()]
        y_data_avg = np.average(y_data)
        x_data_array = [list(packet_time_hist.keys()), list(packet_time_hist.keys())]
        y_data_array = [y_data, [y_data_avg] * len(y_data)]

        self.data_plot['line_utilization'] = [x_data_array, y_data_array, y_data_avg, time_interval]

    def heatmap_time_over_flow_size(self, time_interval=0.1):
        flow_size_count_2d, size_to_idx = PlotTG.calulcate_heatmap_data(
            self.packet_array,
            self.flow_array)
        normalized_flow_size_count_2d = flow_size_count_2d / np.sum(flow_size_count_2d, axis=0)
        normalized_flow_size_count_2d[normalized_flow_size_count_2d <= 0] = np.nan
        x_tick_labels = [np.around(time_interval * i, len(str(time_interval))) for i in
                         range(normalized_flow_size_count_2d.shape[1])]
        self.data_plot['heatmap_time_over_flow_size'] = [normalized_flow_size_count_2d.to_json(),  # dataframe
                                                         x_tick_labels,
                                                         time_interval]

    def plot_flow_duration_cdf(self):
        packet_per_flow = PlotTG.calculate_packet_per_flow(self.packet_array)
        data = [packet_per_flow[flow][-1] - packet_per_flow[flow][0] for flow in packet_per_flow]
        self.data_plot['plot_flow_duration_cdf'] = data

    def plot_flow_duration_over_time(self, percent_threshold=0.001):
        packet_per_flow = PlotTG.calculate_packet_per_flow(self.packet_array)
        filtered_packer_per_flow = {}
        sorted_duration = sorted([packet_per_flow[flow][-1] - packet_per_flow[flow][0] for flow in packet_per_flow],
                                 reverse=True)
        index_of_threshold_duration = int((len(sorted_duration) * percent_threshold))
        data_dict = {}
        for flow in packet_per_flow:
            if packet_per_flow[flow][-1] - packet_per_flow[flow][0] > sorted_duration[index_of_threshold_duration]:
                filtered_packer_per_flow[flow] = packet_per_flow[flow]

        print("max duration: " + str(sorted_duration[0]))
        data_dict['category'] = [str(flow) for flow in filtered_packer_per_flow]
        data_dict['lower'] = [packet_per_flow[flow][0] for flow in filtered_packer_per_flow]
        data_dict['upper'] = [packet_per_flow[flow][-1] for flow in filtered_packer_per_flow]

        self.data_plot['plot_flow_duration_over_time'] = data_dict

    def plot_unique_and_overlap_rules(self, time_slice=0.1):
        clock = 0
        clock_array = [clock]
        unique_rules_count = {}
        overlapping_rules = {}
        non_overlapping_rules = {}
        new_time_slice_flows = set()
        last_time_slice_flows = set()
        for packet in self.packet_array:
            src, dst, size, time, id = packet
            if time > clock + time_slice:
                clock = clock + time_slice
                clock_array.append(clock)
                unique_rules_count[clock] = len(new_time_slice_flows)
                overlapping_rules[clock] = len(new_time_slice_flows.intersection(last_time_slice_flows))
                non_overlapping_rules[clock] = len(new_time_slice_flows - last_time_slice_flows)
                last_time_slice_flows = new_time_slice_flows
                new_time_slice_flows = set()
            rule = dst
            new_time_slice_flows.add(rule)
        y_data_array = [list(unique_rules_count.values()),
                        list(overlapping_rules.values()),
                        list(non_overlapping_rules.values())]
        x_data_array = [clock_array[:-1]] * len(y_data_array)
        y_label = "Uniqe Rules Count"
        x_label = "Time (time slice = " + str(time_slice)
        title = "Unique  and overlapping rules count over time"
        line_description_array = ['unique rules count', 'overlapping rules', 'non overlapping rules']
        self.data_plot['plot_unique_and_overlap_rules'] = [x_data_array,
                                                           y_data_array,
                                                           x_label,
                                                           y_label,
                                                           title,
                                                           line_description_array]

    def plot_flow_duration_by_percent_bucketing(self, time_interval=0.1):
        packet_per_flow = PlotTG.calculate_packet_per_flow(self.packet_array)
        sorted_duration = sorted(
            [(flow, float(packet_per_flow[flow][-1]) - float(packet_per_flow[flow][0])) for flow in packet_per_flow],
            key=lambda x: x[1], reverse=True)
        index_of_first_0 = 64
        for i in range(len(sorted_duration)):
            if sorted_duration[i][1] == 0:
                index_of_first_0 = i
                break
        bucket_0 = index_of_first_0 / len(sorted_duration) * 100
        buckets = [1, 4, 16, 32, bucket_0, 100]
        start = 0
        flow_to_bucket = {}
        bucket_duration_average = []
        for bucket in buckets:
            end = int(
                len(sorted_duration) * (bucket / 100))  # take the (start, end) of the flow from the sorted_duration
            print("(" + str(start) + "," + str(end) + ")")
            for flow, flow_duration in sorted_duration[start:end]:
                flow_to_bucket[flow] = bucket
            bucket_duration_average.append(np.average([v[1] for v in sorted_duration[start:end]]))
            start = end

        conseq_data, conseq_data_per_bucket = PlotTG.calculate_unique_flow_count_data_per_bucket(self.packet_array,
                                                                                                 flow_to_bucket,
                                                                                                 buckets)

        x_data_array = [list(conseq_data.keys())]
        y_data_array = [list(conseq_data.values())]
        y_label = "Uniqe Flow Count By Buckets"
        x_label = "Time (time slice = " + str(time_interval) + ")"
        line_description_array = ["Total"]

        last_bucket = 0
        for bucket, avg_time in zip(conseq_data_per_bucket, bucket_duration_average):
            x_data_array.append(list(conseq_data_per_bucket[bucket].keys()))
            y_data_array.append(list(conseq_data_per_bucket[bucket].values()))
            line_description_array.append(
                "(" + str(round(last_bucket, 2)) + "," + str(
                    round(bucket, 2)) + ") average flow duration: " + "%.2g" % avg_time + " sec")
            last_bucket = bucket
        title = "Unique Flow Count Over Time By Bucket"

        self.data_plot['plot_flow_duration_by_percent_bucketing'] = [x_data_array,
                                                                     y_data_array,
                                                                     x_label,
                                                                     y_label,
                                                                     title,
                                                                     line_description_array]

    def plot_trace_burstiness(self):
        last_packet_dst = None
        burst = {}
        burst_idx = 0
        burst_over_time = {}
        for time_idx, packet in enumerate(self.packet_array):
            if packet[packet_dst_idx] == last_packet_dst:  # burst in progress
                burst[burst_idx] += 1
            else:
                burst_idx += 1
                burst[burst_idx] = 1
                last_packet_dst = packet[packet_dst_idx]
            burst_over_time[time_idx] = burst[burst_idx]
        x_label = "Burst Index"
        y_label = "Burst Size (packets)"
        title = "Trace Burst"
        x_data_array = [list(burst_over_time.keys())]
        y_data_array = [list(burst_over_time.values())]

        self.data_plot['plot_trace_burstiness'] = [x_data_array,
                                                   y_data_array,
                                                   x_label,
                                                   y_label,
                                                   title,
                                                   ['']]


class PlotTrace:
    @staticmethod
    def file_pdf_vs_traffic_generator_pdf(data, scale='log'):
        x_data, y_data = data

        fig = PlotTG.plot_multiple_scatters(x_data, y_data, "Flow Size", "Probability (PDF)",
                                            "File PDF vs Traffic Generator PDF (packet level)", ["File PDF", "TG PDF"],
                                            scale=scale)
        figs_to_save['file_pdf_vs_traffic_generator_pdf'] = fig

    @staticmethod
    def file_cdf_vs_traffic_generator_cdf(data):
        flow_size, cdf_file_path = data
        fig = PlotTG.plot_cdf(flow_size, "sample size", "Path CDF - Pr(sample <= size)", cdf_file_path)
        figs_to_save['file_cdf_vs_traffic_generator_cdf'] = fig

    @staticmethod
    def flow_id_bar_size(data):
        color_by_size, flow_colors, bar_data = data
        fig, ax = plt.subplots()
        ax.set_title("Flow Size By ID")
        ax.bar(bar_data[0], bar_data[1], 1)
        for i in range(len(bar_data[0])):
            if i % 1000 == 0:
                print(i)
            ax.get_children()[i].set_color(flow_colors[i])
        ax.set_xlabel("Flow ID")
        ax.set_ylabel("Packet count")
        fig.tight_layout()

        figs_to_save['flow_id_bar_size'] = fig

    @staticmethod
    def packet_from_size_pdf_cdf(data, reference_data_path=None):
        packet_from_size_pdf, packet_from_size_cdf = data
        pdf_x = [int(key) for key in packet_from_size_pdf.keys()]

        PlotTG.plot_multiple_scatters([pdf_x], [packet_from_size_pdf.values()], "Flow Size",
                                      "Probability (PDF)", "Probability For Receiving Packet From Flow Size (PDF)",
                                      [''], scale='log')
        cdf_x = [int(key) for key in packet_from_size_cdf.keys()]
        fig = PlotTG.plot_multiple_scatters([cdf_x], [packet_from_size_cdf.values()], "Flow Size",
                                            "Probability (CDF)",
                                            "Probability For Receiving Packet From Flow Size (CDF)",
                                            [''], scale='linear')

        figs_to_save['packet_from_size_pdf_cdf'] = fig

    @staticmethod
    def line_utilization(data):
        x_data_array, y_data_array, y_data_avg, time_interval = data
        fig = PlotTG.plot_multiple_lines(x_data_array,
                                         y_data_array,
                                         "Arrival Time - Time Interval: " + str(time_interval),
                                         'Line Utilization (%)',
                                         'Line Utilization Over Time - Average: ' + "{:.2f}".format(y_data_avg) + "%",
                                         ['Utilization In Time Interval',
                                          'Average Utilization'])
        figs_to_save['line_utilization'] = fig

    @staticmethod
    def heatmap_time_over_flow_size(data):
        normalized_flow_size_count_2d_json, x_tick_labels, time_interval = data
        normalized_flow_size_count_2d = pd.read_json(normalized_flow_size_count_2d_json)
        fig, ax = plt.subplots()
        sns.heatmap(normalized_flow_size_count_2d,
                    xticklabels=x_tick_labels,
                    cmap="icefire")
        ax.set_xlabel("Arrival Time - Time Interval: " + str(time_interval))
        ax.set_ylabel("Flow Size (Log2 scale)")
        ax.set_xticks(ax.get_xticks()[::100])
        figs_to_save['heatmap_time_over_flow_size'] = fig

    @staticmethod
    def unique_flow_count(data):
        conseq_data, time_interval = data
        float_conseq_data = {float(key): conseq_data[key] for key in conseq_data.keys()}
        fig = PlotTG.plot_xy(float_conseq_data.keys(), float_conseq_data.values(),
                             "Arrival Time - Time Interval: " + str(time_interval),
                             'Unique Flow Count', 'Unique Flow Count Extracted From Packets')
        figs_to_save['unique_flow_count'] = fig

    @staticmethod
    def plot_flow_duration_cdf(data):
        print("Flow Duration Mean: " + str(np.mean(data)))
        print("Flow Duration Max: " + str(np.max(data)))

        fig = PlotTG.plot_cdf(data, data_x="Time", data_title="Flow duration", reference_data_path=None)
        figs_to_save['plot_flow_duration_cdf'] = fig

    @staticmethod
    def plot_flow_duration_over_time(data):
        dataset = pd.DataFrame(data)
        fig, ax = plt.subplots()
        for lower, upper, y in zip(dataset['lower'], dataset['upper'], range(len(dataset))):
            ax.plot((lower, upper), (y, y), 'ro-', color='orange')
        ax.set_yticks(range(len(dataset)), list(dataset['category']))
        ax.set_xlabel("Time", fontsize=xy_label_font_size)
        ax.set_ylabel("Flow", fontsize=xy_label_font_size)
        # 0.001
        ax.set_title("Flow Life Span Over Time (Longest 1%)", fontsize=title_font_size)
        ax.tick_params(labelsize=xy_tick_font_size)
        figs_to_save['plot_flow_duration_over_time'] = fig

    @staticmethod
    def plot_unique_and_overlap_rules(data):
        x_data_array, y_data_array, x_label, y_label, title, line_description_array = data
        fig = PlotTG.plot_multiple_lines(x_data_array, y_data_array, x_label, y_label, title, line_description_array)
        figs_to_save['plot_unique_and_overlap_rules'] = fig

    @staticmethod
    def plot_flow_duration_by_percent_bucketing(data):
        x_data_array, y_data_array, x_label, y_label, title, line_description_array = data
        fig = PlotTG.plot_multiple_lines(x_data_array, y_data_array, x_label, y_label, title, line_description_array)
        figs_to_save['plot_flow_duration_by_percent_bucketing'] = fig

    @staticmethod
    def plot_trace_burstiness(data):
        x_data_array, y_data_array, x_label, y_label, title, line_description_array = data
        fig = PlotTG.plot_multiple_scatters(x_data_array, y_data_array, x_label, y_label, title, line_description_array)
        figs_to_save['plot_trace_burstiness'] = fig


def run_plot_data_preprocess(plot_data):
    global plot_list
    for plot in plot_list:
        eval("plot_data." + plot + "()")
    pass


def run_plot_trace(plot_data):
    global plot_list
    for plot in plot_list:
        eval("PlotTrace." + plot + "(plot_data.data_plot[\"" + plot + "\"])")
    pass


def main():
    work_dir = sys.argv[-1]

    # Generate JSON file
    plot_data = PlotData(None, #work_dir + 'flow_trace.json',
                         None, #work_dir + 'flowlet_trace.json',
                         work_dir + 'packet_trace.json')
    plot_data.plot_trace_burstiness()
    run_plot_data_preprocess(plot_data)
    plot_data.to_json(work_dir + 'plot_trace.json')

    # Plot JSON file
    plot_data_output = PlotData(
        json_path=work_dir + 'plot_trace.json')
    run_plot_trace(plot_data_output)

    # Save Figures
    file_path = '../Figures/' + work_dir.split('/')[-2] + '/'
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    for fig_name in figs_to_save:
        fig = figs_to_save[fig_name]
        fig.set_size_inches(42, 24)
        fig.savefig(file_path + fig_name, dpi=300)


if __name__ == "__main__":
    main()
