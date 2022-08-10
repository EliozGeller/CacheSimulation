import pandas as pd
import os
import numpy as np
from SimulatorIO import SimulatorIO
from PlotCacheSimulator import PlotCacheSimulator, JoinedTraceExperiment, SingleTraceExperiment, ExperimentConfig
from TGDriverCode.PlotTrace import PlotData, run_plot_data_preprocess
from TimeSeriesLogger import EventType
import json
import matplotlib.pyplot as plt
import seaborn as sns

time_idx = 3
xy_label_font_size = 48
title_font_size = 48
xy_tick_font_size = 36

# global
selected_exp = [
    "websearch_n_flows1000_back2back100000000_flow_per_sec50_flowlet_per_sec1",
    "pareto_n_flows1000_back2back100000000_flow_per_sec10_flowlet_per_sec1",
    "FB_Hadoop_Inter_Rack_FlowCDF_n_flows1000_back2back100000000_flow_per_sec50_flowlet_per_sec1",
    "datamining_n_flows1000_back2back100000000_flow_per_sec30_flowlet_per_sec1"
]


def create_experiment_name_key(exp_name):
    # return exp_name
    param_value = exp_name.split('_')[-7].split('param')[1]
    trace_name = exp_name.split('_')[0]
    return trace_name + '_' + param_value
    # experiment_names_dict[trace_name + '_' + param_value + '_' + str(idx)] = exp_name


def create_experiment_names_dict(experiment_name_array):
    experiment_names_dict = {}
    for idx, exp_name in enumerate(experiment_name_array):
        name_key = create_experiment_name_key(exp_name)
        experiment_names_dict[name_key] = exp_name
        # experiment_names_dict["_".join([str(idx), trace_name])] = exp_name

    return experiment_names_dict


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class CombineCSV:
    def __init__(self):
        self.df = pd.DataFrame()

    def add_df(self, csv_path, experiment_name):
        df = pd.read_csv(csv_path)
        df['Experiment Name'] = [experiment_name] * int(df.shape[0])
        self.df = pd.concat([self.df, df])

    def save_new_csv(self, path_to_save):
        self.df.to_csv(path_to_save)


class AnalyzeBestFixedThresholdPerQuanta:

    @staticmethod
    def apply_function_on_data_by_quanata(vline_data_x, time_slice, input_data, apply_func=np.average):
        processed_data = []
        prev_idx = 0
        if vline_data_x[0] == 0:
            vline_data_x = vline_data_x[1:]
        for i in vline_data_x:
            idx = int(i / time_slice)
            processed_data += [apply_func(input_data[prev_idx:idx])] * (int((idx - prev_idx)))
            prev_idx = idx
        processed_data += [apply_func(input_data[prev_idx:len(input_data)])] * (int((len(input_data) - prev_idx)))
        return processed_data

    @staticmethod
    def plot_analyze_best_fixed_per_quanta(fixed_work_dir, trace_dir, exp_name, quanta):
        data = {}
        data_point_count = -1
        base_exp_dir = fixed_work_dir + exp_name + '/'
        json_path_list = list(filter(lambda s: "(30, 0)" in s, os.listdir(base_exp_dir)))
        for json_path in json_path_list:
            with open(base_exp_dir + json_path, 'r') as f:
                switch_logger_idx = 'switch.logger.event_logger'
                time_slice_idx = 'switch.logger.time_slice'
                json_data = list(json.load(f).values())[0]
                data[json_path.split('_')[2]] = {'cache_hit': json_data[switch_logger_idx]['cache_hit'],
                                                 'time_slice': json_data[time_slice_idx]['cache_hit'],
                                                 'controller_bw': json_data[switch_logger_idx]['controller_bw']}
                if data_point_count > 0 and data_point_count != len(json_data[switch_logger_idx]['cache_hit']):
                    print("Error: Logger size should be the same for all threshold!")
                else:
                    data_point_count = len(json_data[switch_logger_idx]['cache_hit'])

        best_threshold_array = []
        controller_bw_array = []
        vline_data_x = []
        for i in range(0, data_point_count, int(quanta / 0.1)):
            max_avg_cache_hit_per_quanta = -1
            best_threshold_per_quanta = -1
            for threshold in data:
                cache_hit_array = data[threshold]['cache_hit']
                time_slice = data[threshold]['time_slice']

                sum_hit_rate = np.sum(cache_hit_array[i:i + int(quanta / time_slice)])
                if sum_hit_rate > max_avg_cache_hit_per_quanta:
                    max_avg_cache_hit_per_quanta = sum_hit_rate
                    best_threshold_per_quanta = threshold
            if len(best_threshold_array) > 0 and int(best_threshold_per_quanta) != int(best_threshold_array[-1]):
                vline_data_x.append(i * time_slice)

            best_threshold_array += [int(best_threshold_per_quanta)] * int(quanta / time_slice)
            controller_bw_array += data[best_threshold_per_quanta]['controller_bw'][i:i + int(quanta / time_slice)]

        plot_data_output = PlotData(
            json_path=trace_dir + exp_name + '/plot_trace.json')

        # best_threshold_array = best_threshold_array[:-int(quanta / time_slice)]
        line_rate = 100000
        effective_line_rate = line_rate * time_slice
        controller_norm = [100 * (value / effective_line_rate) for value in controller_bw_array]

        x_utilization, y_utilization, y_data_avg, time_interval = plot_data_output.data_plot['line_utilization']
        util_array = y_utilization[0]

        conseq_data, time_interval = plot_data_output.data_plot['unique_flow_count']
        float_conseq_data = {float(key): conseq_data[key] for key in conseq_data.keys()}
        unique_flow_array = list(float_conseq_data.values())

        return best_threshold_array, controller_norm, util_array, unique_flow_array, time_slice, vline_data_x

    @staticmethod
    def calculate_hypothesis_probability(vline_data_x, time_slice, best_threshold_array, avg_per_quanta_array):
        hypothesis = {}

        prev_idx = 0
        for i in vline_data_x:
            idx = int(i / time_slice)
            if idx == len(avg_per_quanta_array):
                idx -= 1
            threshold_change = int(best_threshold_array[idx]) - int(best_threshold_array[prev_idx])
            change_in_avg_per_quanta = avg_per_quanta_array[idx] - avg_per_quanta_array[prev_idx]
            prev_idx = idx

            if change_in_avg_per_quanta < 0 and threshold_change < 0:  # 00
                hypothesis['(-)->-'] = 1 + hypothesis.get('(-)->-', 0)

            elif change_in_avg_per_quanta < 0 and threshold_change > 0:  # 01
                hypothesis['(-)->+'] = 1 + hypothesis.get('(-)->+', 0)

            elif change_in_avg_per_quanta > 0 and threshold_change < 0:  # 10
                hypothesis['(+)->-'] = 1 + hypothesis.get('(+)->-', 0)

            elif change_in_avg_per_quanta > 0 and threshold_change > 0:  # 11
                hypothesis['(+)->+'] = 1 + hypothesis.get('(+)->+', 0)

            else:
                print("change_in_avg_per_quanta: {0} threshold_change: {1}".format(change_in_avg_per_quanta,
                                                                                   threshold_change))
                hypothesis['DC'] = 1 + hypothesis.get('DC', 0)
        return {h: 100 * hypothesis[h] / len(vline_data_x) for h in hypothesis}

    @staticmethod
    def organize_and_plot_multiple_lines(fixed_work_dir, trace_dir, exp_name, quanta, file_path):
        best_threshold_array, controller_norm, util_array, unique_flow_array, time_slice, vline_data_x = \
            AnalyzeBestFixedThresholdPerQuanta.plot_analyze_best_fixed_per_quanta(fixed_work_dir,
                                                                                  trace_dir,
                                                                                  exp_name,
                                                                                  quanta)

        avg_unique_flow_array = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                                     time_slice,
                                                                                                     unique_flow_array)
        avg_util_array = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                              time_slice,
                                                                                              util_array)
        avg_controller_bw = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                                 time_slice,
                                                                                                 controller_norm)

        x_label_array = ["Time Slice: {0}".format(time_slice)] * 4
        y_label_array = ['Threshold', 'BW (%)', 'BW (%)', 'Unique Flow Count']
        title_array = ["FixedThredhold - Experiment {0} Time Quanta: {1}".format(exp_name, quanta),
                       "Controller BW",
                       "Line Utilization",
                       "Unique Flow Count"]

        data_y_array = [(controller_norm, avg_controller_bw),
                        (util_array, avg_util_array),
                        (unique_flow_array, avg_unique_flow_array)]
        data_x_array = [(np.arange(0, len(array[0]) * time_slice, time_slice),
                         np.arange(0, len(array[1]) * time_slice, time_slice))
                        for array in data_y_array]

        data_y_array = [(best_threshold_array, None)] + data_y_array
        data_x_array = [(np.arange(0, len(best_threshold_array) * time_slice, time_slice), None)] + data_x_array

        fig = PlotCacheSimulator.plot_analyze_best_fixed_per_quanta(data_x_array, data_y_array, x_label_array,
                                                                    y_label_array, title_array, vline_data_x)

        fig.set_size_inches(42, 24)
        path_to_save = file_path + 'BestFixedThresholdPerQuanta_{0}_{1}'.format(quanta, exp_name) + '.jpg'
        print(path_to_save)
        ensure_dir(path_to_save)
        fig.savefig(path_to_save, dpi=300)

    @staticmethod
    def plot_hypothesis_bar(fixed_work_dir, trace_dir, exp_name, quanta, file_path):
        best_threshold_array, controller_norm, util_array, unique_flow_array, time_slice, vline_data_x = \
            AnalyzeBestFixedThresholdPerQuanta.plot_analyze_best_fixed_per_quanta(fixed_work_dir,
                                                                                  trace_dir,
                                                                                  exp_name,
                                                                                  quanta)

        avg_unique_flow_array = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                                     time_slice,
                                                                                                     unique_flow_array)
        avg_util_array = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                              time_slice,
                                                                                              util_array)
        avg_controller_bw = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                                 time_slice,
                                                                                                 controller_norm)

        controller_bw_hypothesis = AnalyzeBestFixedThresholdPerQuanta.calculate_hypothesis_probability(vline_data_x,
                                                                                                       time_slice,
                                                                                                       best_threshold_array,
                                                                                                       avg_controller_bw)

        line_util_hypothesis = AnalyzeBestFixedThresholdPerQuanta.calculate_hypothesis_probability(vline_data_x,
                                                                                                   time_slice,
                                                                                                   best_threshold_array,
                                                                                                   avg_util_array)

        unique_flow_array_hypothesis = AnalyzeBestFixedThresholdPerQuanta.calculate_hypothesis_probability(vline_data_x,
                                                                                                           time_slice,
                                                                                                           best_threshold_array,
                                                                                                           avg_unique_flow_array)

        data_x = ['controller bw', 'line utilization', 'unique flow count']

        hypothesis = np.unique(list(controller_bw_hypothesis.keys()) + list(line_util_hypothesis.keys()) + list(
            unique_flow_array_hypothesis.keys()))
        hypothesis_array = [controller_bw_hypothesis, line_util_hypothesis, unique_flow_array_hypothesis]

        for hyp in hypothesis:
            for hyp_dict in hypothesis_array:
                if hyp not in hyp_dict:
                    hyp_dict[hyp] = 0

        title = "Experiment: {0} - Time Quanata: {1}".format(exp_name, quanta)
        fig = PlotCacheSimulator.plot_hypothesis_bar(hypothesis_array, data_x, title)

        fig.set_size_inches(42, 24)
        path_to_save = file_path + 'Hypothesis_count_{0}_{1}'.format(quanta, exp_name) + '.jpg'
        print(path_to_save)
        ensure_dir(path_to_save)
        print(path_to_save)
        fig.savefig(path_to_save, dpi=300)


class AnalyzeDyanmicThresholdQuanta:
    @staticmethod
    def parse_exp_json_data(exp_json_path):

        with open(exp_json_path, "r") as f:
            exp_data = json.load(f)

        exp_data_logger_dict = list(exp_data.values())[0]
        unique_rules_count_sample = exp_data_logger_dict['insertion_algorithm.logger.event_logger']['unique_flow']
        threshold_array = exp_data_logger_dict['insertion_algorithm.logger.event_logger']['threshold']
        time_slice = exp_data_logger_dict['switch.logger.time_slice']['controller_bw']
        epoch = float(exp_data_logger_dict['switch.controller.insertion_algorithm.column_data']['Epoch'])
        x_label_array = ['Time - {0} sec'.format(time_slice)] * 2
        algorithm_name = exp_data_logger_dict['switch.controller.insertion_algorithm.column_data']['In.']
        y_label_array = ['Threshold', 'Unique Flow Count'] if len(unique_rules_count_sample
                                                                  ) > 0 else ['Threshold', 'BW Sample (controller) (%)']
        title_array = ['Threshold Value Over Time - Epoch {0} \n {1}'.format(epoch,
                                                                             algorithm_name)]
        title_array += ['Unique Flow Count'] if len(unique_rules_count_sample) > 0 else ['Controller BW (Sample)']
        signal_input_data = unique_rules_count_sample if len(unique_rules_count_sample
                                                             ) > 0 else exp_data_logger_dict[
            'insertion_algorithm.logger.event_logger']['controller_bw']
        return unique_rules_count_sample, threshold_array, signal_input_data, \
               time_slice, epoch, x_label_array, y_label_array, title_array

    @staticmethod
    def plot_dynamic_threshold_experiment_from_json(exp_json_path):
        unique_rules_count_sample, threshold_array, signal_input_data, time_slice, epoch, \
        x_label_array, y_label_array, title_array = AnalyzeDyanmicThresholdQuanta.parse_exp_json_data(exp_json_path)
        if len(unique_rules_count_sample) > 0:
            AnalyzeDyanmicThresholdQuanta.plot_by_signal(threshold_array, signal_input_data, time_slice, epoch,
                                                         x_label_array, y_label_array, title_array, None, np.max)
        else:
            AnalyzeDyanmicThresholdQuanta.plot_by_signal(threshold_array, signal_input_data, time_slice,
                                                         epoch, x_label_array, y_label_array, title_array,
                                                         None, np.average)

    @staticmethod
    def plot_by_signal(dynamic_threshold, fixed_threshold, signal_input_data, time_slice, epoch, x_label_array,
                       y_label_array, title_array, file_path, apply_quanta_func, line_description_array):
        vline_data_x = []
        data_point_count = len(signal_input_data)
        epoch_count = 0
        fill_dynamic_threshold = []
        for i in range(0, data_point_count, int(epoch / 0.1)):
            vline_data_x.append(epoch_count)
            epoch_count += epoch
            max_th_in_epoch = max(dynamic_threshold[i:i + int(epoch / 0.1)])
            next_value = max_th_in_epoch if max_th_in_epoch > 0 else fill_dynamic_threshold[-1]
            fill_dynamic_threshold = fill_dynamic_threshold + [next_value] * int(epoch / 0.1)
        input_data_avg = AnalyzeBestFixedThresholdPerQuanta.apply_function_on_data_by_quanata(vline_data_x,
                                                                                              time_slice,
                                                                                              signal_input_data,
                                                                                              apply_quanta_func)

        data_y_array = [(fill_dynamic_threshold, fixed_threshold)] + [(signal_input_data, input_data_avg)]

        data_x_array = [(list(range(len(fill_dynamic_threshold))), list(range(len(fixed_threshold))))] + \
                       [(list(range(len(signal_input_data))),
                         list(range(len(input_data_avg))))]

        # def plot_analyze_best_fixed_per_quanta(data_x_array, data_y_array, x_label_array, y_label_array, title_array,
        # vline_data_x=None)
        fig = PlotCacheSimulator.plot_analyze_best_fixed_per_quanta(data_x_array,
                                                                    data_y_array,
                                                                    x_label_array,
                                                                    y_label_array,
                                                                    title_array,
                                                                    line_description_array,
                                                                    [x / time_slice for x in vline_data_x])

        fig.set_size_inches(42, 24)
        print(file_path)
        ensure_dir(file_path)
        fig.savefig(file_path, dpi=300)
        plt.clf()

    @staticmethod
    def plot_dynamic_threshold_json_and_static_threshold_per_quanta(exp_json_path, fixed_work_dir, trace_dir, exp_name,
                                                                    file_path):
        unique_rules_count_sample, dynamic_threshold, signal_input_data, time_slice, epoch, \
        x_label_array, y_label_array, title_array = AnalyzeDyanmicThresholdQuanta.parse_exp_json_data(exp_json_path)

        fixed_threshold, controller_norm, util_array, unique_flow_array, time_slice, vline_data_x = \
            AnalyzeBestFixedThresholdPerQuanta.plot_analyze_best_fixed_per_quanta(fixed_work_dir,
                                                                                  trace_dir,
                                                                                  exp_name,
                                                                                  epoch)

        if len(unique_rules_count_sample) > 0:
            line_description_array = [("Dynamic Threshold", "Fixed Threshold"), ('Unique Rules', 'Unique Rules (max)')]
            AnalyzeDyanmicThresholdQuanta.plot_by_signal(dynamic_threshold, fixed_threshold, signal_input_data,
                                                         time_slice, epoch, x_label_array, y_label_array,
                                                         title_array, file_path, np.max, line_description_array)
        else:
            line_description_array = [("Dynamic Threshold", "Fixed Threshold"),
                                      ('Controller BW (Sample)', 'Controller BW (Average)')]
            AnalyzeDyanmicThresholdQuanta.plot_by_signal(dynamic_threshold, fixed_threshold, signal_input_data,
                                                         time_slice,
                                                         epoch, x_label_array, y_label_array, title_array,
                                                         file_path, np.average, line_description_array)


class CompareCompleteSummary:
    @staticmethod
    def create_complete_summary_csv(input_path):
        csv_path_array = []
        for path, subdirs, files in os.walk(input_path):
            for name in files:
                if 'all_experiments.csv' in name:
                    csv_path_array.append(os.path.join(path, name))
        print(csv_path_array)
        combine_csv = CombineCSV()
        for csv_path in csv_path_array:
            experiment_name = csv_path.split('/')[-2]
            combine_csv.add_df(csv_path, experiment_name)

        print(input_path + 'complete_summary.csv')
        combine_csv.save_new_csv(input_path + '/complete_summary.csv')
        print(input_path + '/complete_summary.csv')

    @staticmethod
    def plot_bar_best_main_secondary_cache_over_trace(complete_summary_csv_path, experiment_names_dict):
        df = pd.read_csv(complete_summary_csv_path)
        save_fig_path = 'Figures/main_secondary_cmp/'
        ensure_dir(save_fig_path)
        result_summary = {n: [] for n in experiment_names_dict.keys()}
        for experiment_name in experiment_names_dict.values():
            for main_sz, secondary_sz in [(0, 500), (100, 400), (250, 250), (400, 100), (500, 0)]:
                sub_df = df[(df['Main Cache Size'] == main_sz) &
                            (df['Secondary Cache Size'] == secondary_sz) &
                            (df['Experiment Name'] == experiment_name)]
                result_df = sub_df[(sub_df['Total Hits Percent'] ==
                                    sub_df['Total Hits Percent'].max())]
                for k, v in experiment_names_dict.items():
                    if v == experiment_name:
                        if len(result_df['Total Hits Percent'].values) > 1:
                            print("ERROR: more than one result")
                        result_summary[k].append(((main_sz, secondary_sz),
                                                  max(result_df['Threshold'].values),
                                                  max(result_df['Total Hits Percent'].values)))

        for trace_nickname in result_summary:
            fig, ax = plt.subplots()
            data_y = [v[-1] for v in result_summary[trace_nickname]]
            data_x = [str(v[0]) for v in result_summary[trace_nickname]]
            ax.bar(data_x, data_y, color='g')
            ax.set_ylabel("Total Hits %")
            ax.set_xlabel("Cache Size (Main, Secondary)")
            ax.set_title("Trace: {0}".format(trace_nickname))
            annot_array = ["Th:{0}".format(v[1]) for v in result_summary[trace_nickname]]
            for i in range(len(annot_array)):
                plt.annotate(str(annot_array[i]), xy=(data_x[i], data_y[i]), ha='center', va='bottom')
            file_name = 'Main' + '_' + 'Secondary' + trace_nickname + '.png'
            fig.savefig(save_fig_path + file_name, dpi=300)

    @staticmethod
    def get_best_results_from_complete_summary(work_dir):
        complete_summary_csv = work_dir + '/complete_summary.csv'
        df = pd.read_csv(complete_summary_csv)
        experiment_names = np.unique(df['Experiment Name'])
        main_cache_size_array = np.unique(df['Main Cache Size'])
        result_df = pd.DataFrame()

        for cz in main_cache_size_array:
            cz_df = df[(df['Main Cache Size'] == cz)]
            for exp_name in experiment_names:
                exp_df = cz_df[(cz_df['Experiment Name'] == exp_name)]
                best_row = exp_df[(exp_df['Total Hits Percent'] ==
                                   exp_df['Total Hits Percent'].max())]
                best_row = best_row[(best_row['Threshold'] == best_row['Threshold'].min())]
                result_df = pd.concat([result_df, best_row])
            result_df.to_csv(work_dir + '/best_results.csv')
        print("s")

    @staticmethod
    def get_annotation_name(hit_rate, algo_in, algo_evic, threhsold, epoch):
        long_to_short = {'DTHillClimberBW_0.01_0.5': "HBW",
                         'DTHillClimberUniqueFlows_0.01_0.5': 'HUF',
                         'DynamicThresholdBW0.01_0.5': 'DBW',
                         'DynamicThresholdUniqueFlow0.01_0.5': 'DUF'
                         }

        # FixedThreshold
        if algo_in == 'FixedThreshold' and int(threhsold) > 1:
            return threhsold, 'g'

        # ClassicAlgorithm
        if algo_in == 'FixedThreshold' and algo_evic != 'Random':
            return algo_evic, 'b'

        # DynamicAlgorithm
        return long_to_short[algo_in] + str(epoch), 'r'

    @staticmethod
    def compare_dynamic_as_bar_static_as_dot(complete_summary):
        df = pd.read_csv(complete_summary)
        experiment_name_array = np.unique(df['Experiment Name'])
        # short_experiment_name = {v: k for k, v in create_experiment_names_dict(experiment_name_array).items()}
        # df = df[df['Experiment Name'].isin(selected_exp)]
        dynamic_algorithm_array = list(np.unique(df[(df['In.'] != "FixedThreshold")]['In.']))
        # experiment_name_array = selected_exp

        conf_arr = []
        for index, row in df.iterrows():
            conf_arr.append((row['Main Cache Size'], row['Secondary Cache Size']))

        cache_sizes = [[(0, 2), (1, 1), (2, 0)], [(0, 10), (5, 5), (10, 0)], [(0, 30), (15, 15), (30, 0)]]

        """
        for cache_conf in cache_sizes:
            cache_conf_res = {}
            best_threshold_param_all = []
            for mcs, scs in cache_conf:
                fig_result = {}
                best_threshold_param = []
                for experiment_name in experiment_name_array:
        """

        for cache_conf in cache_sizes:
            for dynamic_algorithm in list(filter(lambda name: "BW" in name, dynamic_algorithm_array)):
                for epoch in np.unique(df['Epoch'])[:-1]:
                    cache_conf_res = {}
                    for mcs, scs in cache_conf:
                        fig_result = {}
                        for experiment_name in experiment_name_array:
                            fig_df = df[
                                (df['Main Cache Size'] == mcs) &
                                (df['Secondary Cache Size'] == scs) &
                                (df['Experiment Name'] == experiment_name)]

                            fixed_threshold_best = fig_df[(fig_df['In.'] == "FixedThreshold")][
                                'Total Hits Percent'].max()
                            dynamic_threshold_best = fig_df[(fig_df['Epoch'] == epoch) &
                                                            (fig_df['In.'] == dynamic_algorithm)][
                                'Total Hits Percent'].max()
                            fig_result[experiment_name] = (fixed_threshold_best, dynamic_threshold_best)

                        dynamic_algorithm_short_name, color = CompareCompleteSummary.get_annotation_name(0,
                                                                                                         dynamic_algorithm,
                                                                                                         None, 0, epoch)
                        cache_conf_res[(mcs, scs)] = fig_result

                    data_x = [create_experiment_name_key(x) for x in experiment_name_array]
                    data_y = []
                    for res_conf, result_dict in cache_conf_res.items():
                        data_y.append([result_dict[y] for y in experiment_name_array])

                    X_axis = np.arange(len(data_x))
                    fig, ax = plt.subplots()
                    ax.bar(X_axis - 0.3, [y[0] for y in data_y[0]], 0.3, label='{0}'.format(cache_conf[0]))

                    ax.bar(X_axis + 0, [y[0] for y in data_y[1]], 0.3, label='{0}'.format(cache_conf[1]))

                    ax.bar(X_axis + 0.3, [y[0] for y in data_y[2]], 0.3, label='{0}'.format(cache_conf[2]))

                    ax.scatter(list(X_axis - 0.3) + list(X_axis) + list(X_axis + 0.3),
                               [y[1] for y in data_y[0]] +
                               [y[1] for y in data_y[1]] +
                               [y[1] for y in data_y[2]],
                               label='{0}'.format(cache_conf[0]), color='r', s=100)

                    ax.set_xticks(X_axis, data_x, rotation=45, ha='right')
                    ax.set_ylabel("Total Hits %", fontsize=18)
                    ax.set_xlabel("Trace", fontsize=18)
                    ax.set_title("Comparing Static Dyanmic\n (Main, Secondary): {0},{1},{2} \n"
                                 "Algorithm: {3}".format(*cache_conf,
                                                         dynamic_algorithm_short_name),
                                 fontsize=20)
                    ax.legend(["Dynamic"] + ["Static " + str(conf) for conf in cache_conf])

                    ax.grid(True)
                    ax.set_axisbelow(True)
                    fig.set_size_inches(12, 10)
                    base_dir = "Figures/{0}/staticvsdyanmic/{1}/".format(complete_summary.split('/')[-2],
                                                                         dynamic_algorithm_short_name)
                    ensure_dir(base_dir)
                    file_name = '_'.join(['compare',
                                          "{0}{1}{2}".format(*cache_conf),
                                          dynamic_algorithm_short_name,
                                          str(epoch),
                                          '.png'])
                    ax.set_xticklabels(data_x, rotation=45, ha='right')
                    print(file_name)
                    # fig.savefig(base_dir + file_name, dpi=300)
                    plt.clf()
            # break

    @staticmethod
    def compare_best_static_per_configuration(complete_csv):
        df = pd.read_csv(complete_csv)
        df = df[df['In.'] == "FixedThreshold"]
        experiment_name_array = np.unique(df['Experiment Name'])

        conf_arr = []
        for index, row in df.iterrows():
            conf_arr.append((row['Main Cache Size'], row['Secondary Cache Size']))

        cache_sizes = [[(0, 2), (1, 1), (2, 0)], [(0, 10), (5, 5), (10, 0)], [(0, 30), (15, 15), (30, 0)]]

        for cache_conf in cache_sizes:
            cache_conf_res = {}
            best_threshold_param_all = []
            for mcs, scs in cache_conf:
                fig_result = {}
                best_threshold_param = []
                for experiment_name in experiment_name_array:
                    fig_df = df[(df['Main Cache Size'] == mcs) &
                                (df['Secondary Cache Size'] == scs) &
                                (df['Experiment Name'] == experiment_name)]
                    fixed_threshold_best = fig_df['Total Hits Percent'].max()
                    if mcs > 0:
                        best_threshold_param.append(max(fig_df[(fig_df['Total Hits Percent'] == fig_df[
                            'Total Hits Percent'].max())]['Threshold']))
                    else:
                        best_threshold_param.append('')
                    fig_result[experiment_name] = fixed_threshold_best
                cache_conf_res[(mcs, scs)] = fig_result
                best_threshold_param_all.append(best_threshold_param)

            data_x = [create_experiment_name_key(x) for x in experiment_name_array]
            data_y = []
            for res_conf, result_dict in cache_conf_res.items():
                data_y.append([result_dict[y] for y in experiment_name_array])

            X_axis = np.arange(len(data_x))
            fig, ax = plt.subplots()
            ax.bar(X_axis - 0.3, data_y[0], 0.3, label='{0}'.format(cache_conf[0]))
            ax.bar(X_axis + 0, data_y[1], 0.3, label='{0}'.format(cache_conf[1]))
            ax.bar(X_axis + 0.3, data_y[2], 0.3, label='{0}'.format(cache_conf[2]))

            ax.set_xticks(X_axis, data_x, rotation=45, ha='right')
            ax.set_ylabel("Total Hits %", fontsize=18)
            ax.set_xlabel("Trace", fontsize=18)
            ax.set_title(
                "Best Static Result Per Cache Configuration {0}, {1}, {2} (Main, Secondary)".format(*cache_conf)),
            # ax.set_title("Number of Students in each group")
            ax.legend()
            width = 0.3
            for idx, best_threshold_param in enumerate(best_threshold_param_all):
                for i, th in enumerate(best_threshold_param):
                    plt.annotate(th, xy=(X_axis[i] - width, data_y[idx][i]), ha='center', va='bottom', fontsize=12)
                    # barlist[i].set_color(annot_array[i][1])
                width -= 0.3

            ax.grid(True)
            ax.set_axisbelow(True)
            fig.set_size_inches(20, 10)

            file_name = '_'.join(['static_conf', "{0}{1}{2}".format(*cache_conf), '.png'])
            base_dir = "Figures/{0}/static_conf/".format(complete_csv.split('/')[-2])
            ensure_dir(base_dir)
            print(base_dir + file_name)
            fig.savefig(base_dir + file_name, dpi=300)

    @staticmethod
    def find_best_dynamic_threshold_algorithm(complete_summary):
        df = pd.read_csv(complete_summary)
        dynamic_algorithm_array = list(np.unique(df[(df['In.'] != "FixedThreshold")]['In.']))
        epoch_array = np.unique(df[(df['Epoch'] > 0)]['Epoch'])

        hit_sum = {}
        for dynamic_algorithm in dynamic_algorithm_array:
            for epoch in epoch_array:
                df_algo = df[(df['In.'] == dynamic_algorithm) &
                             (df['Epoch'] == epoch) &
                             df['Main Cache Size'].isin([15, 30])]
                hit_sum["_".join([dynamic_algorithm, str(epoch)])] = df_algo['Total Hits Percent'].sum()

        for k, v in sorted(hit_sum.items(), key=lambda v: v[1], reverse=True):
            print("{0} : {1}".format(k, v))
        # print(hit_sum)

    @staticmethod
    def configuration_heatmap(complete_summary, file_path):
        df = pd.read_csv(complete_summary)
        print("s")
        df_tmp = df[(df["In."] == "FixedThreshold")][
            ['Threshold', "Experiment Name", "Main Cache Size", "Secondary Cache Size", "Total Hits Percent"]]
        heatmap_data = {}
        # cache_sizes_array = [[(0, 2), (1, 1), (2, 0)], [(0, 10), (5, 5), (10, 0)], [(0, 30), (15, 15), (30, 0)]]
        cache_sizes_array = [[(0, 30), (15, 15), (30, 0)]]
        # cache_sizes_array = [[(0, 10), (5, 5), (10, 0)]]
        # cache_sizes_array = [[(0, 2), (1, 1), (2, 0)]]

        for experiment_name in np.unique(df['Experiment Name']):
            for cache_sizes in cache_sizes_array:
                for mcs, scs in cache_sizes:
                    df_conf = df_tmp[(df_tmp['Main Cache Size'] == mcs) &
                                     (df_tmp['Secondary Cache Size'] == scs) &
                                     (df_tmp['Experiment Name'] == experiment_name)]
                    for threshold in df_conf['Threshold']:
                        heatmap_data[(threshold, (mcs, scs))] = float(
                            df_conf[(df_conf['Threshold'] == threshold)]["Total Hits Percent"])

                    data = list(map(list, zip(*heatmap_data.keys()))) + [heatmap_data.values()]
                    df_2d = pd.DataFrame(zip(*data)).set_index([0, 1])[2].unstack()
                    df_2d.combine_first(df.T).fillna(0)

                fig, ax = plt.subplots()
                sns.heatmap(df_2d,
                            # xticklabels=x_tick_labels,
                            cmap="rocket_r",
                            annot=True)
                ax.set_xlabel("Cache Configuration (Main, Secondary)")
                ax.set_ylabel("Threshold")
                exp_label = create_experiment_name_key(experiment_name)
                ax.set_title(exp_label)
                ensure_dir(file_path)
                print(file_path + exp_label + '.jpg')
                fig.savefig(file_path + exp_label + '.jpg')
                plt.clf()

    @staticmethod
    def compare_two_complete_summaries(cs_1, cs_2):
        df_cs1 = pd.read_csv(cs_1)
        df_cs2 = pd.read_csv(cs_2)
        experiment_key = ['Threshold', 'Experiment Name']
        req_cols = experiment_key + ['Main Cache Size_x', 'Secondary Cache Size_x', 'Total Hits Percent_x',
                                     'Total Hits Percent_y', 'Cache Conf', 'Cache Conf Epoch']
        # df_cs2['Cache Conf'] = [None]*df_cs2.shape[0]
        # df_cs2['Cache Conf Epoch'] = [None] * df_cs2.shape[0]
        df_res = pd.merge(df_cs1, df_cs2, on=experiment_key)[req_cols]

        # for mcs, scs in df_res[['Main Cache Size_x', 'Secondary Cache Size_x']].drop_duplicates():
        cache_conf_array = [(x, y) for x, y in df_res[['Main Cache Size_x',
                                                       'Secondary Cache Size_x']].drop_duplicates().to_records(
            index=False)]
        # for threshold in np.unique(df_res['Threshold']):
        for dcc_algo in np.unique([df_res['Cache Conf']]):
            res_dict = {}
            for experiment in np.unique(df_res['Experiment Name']):
                cache_conf = {}
                for mcs, scs in cache_conf_array:
                    cache_conf[(mcs, scs)] = df_res[(df_res['Cache Conf'] == dcc_algo) &
                                                    (df_res['Experiment Name'] == experiment) &
                                                    (df_res['Main Cache Size_x'] == mcs) &
                                                    (df_res['Secondary Cache Size_x'] == scs)][
                        ['Total Hits Percent_x', 'Total Hits Percent_y']].to_records(index=False)[0]  # recArray
                res_dict[experiment] = cache_conf

            data_x = list(res_dict.keys())
            X_axis = np.arange(len(data_x))
            fig, ax = plt.subplots()

            ax.bar(X_axis - 0.3, [res_dict[x][cache_conf_array[0]][0] for x in data_x], 0.3,
                   label='{0}'.format(cache_conf_array[0]))

            ax.bar(X_axis + 0, [res_dict[x][cache_conf_array[1]][0] for x in data_x], 0.3,
                   label='{0}'.format(cache_conf_array[1]))

            ax.bar(X_axis + 0.3, [res_dict[x][cache_conf_array[2]][0] for x in data_x], 0.3,
                   label='{0}'.format(cache_conf_array[2]))
            ax.legend(["Static " + str(conf) for conf in cache_conf])

            ax.scatter(X_axis, [res_dict[x][cache_conf_array[0]][1] for x in data_x], color='r', s=100)
            ax.scatter(X_axis - 0.3, [res_dict[x][cache_conf_array[0]][1] for x in data_x], color='r', s=100)
            ax.scatter(X_axis + 0.3, [res_dict[x][cache_conf_array[0]][1] for x in data_x], color='r', s=100)
            for idx, exp_name in enumerate(data_x):
                ax.plot([X_axis[idx] - 0.3, X_axis[idx], X_axis[idx] + 0.3],
                        [res_dict[exp_name][cache_conf_array[0]][1]] * 3,
                        color='r')
            # ax.scatter(list(X_axis - 0.3) + list(X_axis) + list(X_axis + 0.3),
            #            [y[1] for y in data_y[0]] +
            #            [y[1] for y in data_y[1]] +
            #            [y[1] for y in data_y[2]],
            #            label='{0}'.format(cache_conf[0]), color='r', s=100)

            ax.set_xticks(X_axis, [create_experiment_name_key(exp) for exp in data_x], rotation=45, ha='right')
            ax.set_ylabel("Total Hits %", fontsize=18)
            ax.set_xlabel("Trace", fontsize=18)
            ax.set_title("Comparing Static Dynamic Cache Configuration \n Algorithm: {0}".format(dcc_algo),
                         fontsize=20)
            fig_name = 'cache_conf_dyvst_alg{0}.jpg'.format(dcc_algo)
            # fig.set_size_inches(42, 24)
            fig.set_size_inches(20, 10)
            file_path = 'Figures/{0}/cache_conf_dyvst/'.format(cs_2.split('/')[-2])
            ensure_dir(file_path)
            print(file_path + fig_name + '.jpg')
            fig.savefig(file_path + fig_name + '.jpg')
            plt.clf()


def run_full_scheme():
    # assuming they all end with '/'
    base_dir = 'SimulatorTrace/past_experiments/joined2711/'
    fixed_work_dir = base_dir + 'FixedThreshold_2711/'
    joined_dynamic_work_dir = base_dir + 'JoinedTrace_DynamicThreshold_2711/'
    joined_fixed_work_dir = base_dir + 'JoinedTrace_FixedThreshold_2711/'

    csv_compare_file_path = base_dir + 'static_vs_dynamic2711.csv'
    # SimulatorIO.compare_dynamic_and_static(joined_dynamic_work_dir + 'all_experiments.csv',
    #                                        joined_fixed_work_dir + 'all_experiments.csv', csv_compare_file_path)

    joined_experiment = JoinedTraceExperiment(csv_compare_file_path,
                                              joined_dynamic_work_dir,
                                              joined_fixed_work_dir)

    single_trace_dict = {d: SingleTraceExperiment(fixed_work_dir + d + '/') for d in os.listdir(fixed_work_dir)}

    json_path_list = list(
        filter(lambda s: "json" in s and 'trace_times.json' not in s, os.listdir(joined_dynamic_work_dir)))

    file_path = 'Figures/' + base_dir.split('/')[-2] + '/'
    ensure_dir(file_path)
    for json_path in json_path_list:
        with open(joined_dynamic_work_dir + json_path) as f:
            experiment_data = json.load(f)
            for key in experiment_data:
                cache_size, delay = key.split(',')[-1], key.split(',')[-2]
                increase_method = json_path.split('_')[6] + '_' + json_path.split('_')[7]
                decrease_method = json_path.split('_')[8] + '_' + json_path.split('_')[9]

                print(file_path + key + '.jpg')
                fig = PlotCacheSimulator.compare_single_joined_dynamic_experiment_multple_traces(ExperimentConfig(
                    int(cache_size),
                    float(delay)),
                    joined_experiment,
                    experiment_data[key],
                    single_trace_dict,
                    increase_method,
                    decrease_method)
                fig.set_size_inches(42, 24)
                print(file_path + key + '.jpg')
                fig.savefig(file_path + key + '.jpg')
                plt.clf()


def plot_n_best_results_fixed_threshold(n, experiment_names_dict, complete_summary_static, main_cache_size):
    df_static = pd.read_csv(complete_summary_static)
    df_static = df_static[(df_static['Main Cache Size'] == main_cache_size) & (
            df_static['Secondary Cache Size'] == 500 - main_cache_size)]
    for exp_name in experiment_names_dict:
        df1 = df_static[(df_static['Experiment Name'] == experiment_names_dict[exp_name])]
        largest_df_static = df1[['Threshold', 'Total Hits Percent']].nlargest(n - 1, ['Total Hits Percent'])
        res = list(largest_df_static.to_records(index=False))
        res = sorted(res, key=lambda v: v[1])

        fig, ax = plt.subplots()
        data_x = list(range(len(res)))
        data_y = [y[1] for y in res]
        barlist = ax.bar(data_x, data_y, color='g')
        ax.set_ylabel("Total Hits %")
        ax.set_xlabel("Algorithm")
        ax.set_title("Top Algorithm (Cache hit) per trace {0}".format(exp_name))
        annot_array = [y[0] for y in res]
        for i in range(len(annot_array)):
            plt.annotate(str(annot_array[i]), xy=(data_x[i], data_y[i]), ha='center', va='bottom')
        ax.grid(True)
        ax.set_axisbelow(True)
        plt.show()


def plot_n_best_results_bar_plot(n, experiment_names_dict, complete_summary_dynamic, complete_summary_static,
                                 main_cache_size, to_filter):
    df_static = pd.read_csv(complete_summary_static)
    df_static = df_static[(df_static['Main Cache Size'] == main_cache_size) & (
            df_static['Secondary Cache Size'] == 500 - main_cache_size)]

    df_dynamic = pd.read_csv(complete_summary_dynamic)
    df_dynamic = df_dynamic[(df_dynamic['Main Cache Size'] == main_cache_size) & (
            df_dynamic['Secondary Cache Size'] == 500 - main_cache_size)]
    epoch_array = np.unique(df_dynamic['Epoch'])
    insertion_algorithm_name_array = np.unique(df_dynamic['In.'])
    for exp_name in experiment_names_dict:
        for epoch in [5]:  # epoch_array:
            df1 = df_static[(df_static['Experiment Name'] == experiment_names_dict[exp_name])]
            if to_filter:
                best_static_threshold = int(
                    min(df1[(df1['Total Hits Percent'] == df1['Total Hits Percent'].max())]['Threshold']))
                df1 = df1[
                    df1.apply(lambda row: row['Threshold'] in [best_static_threshold + i for i in range(-8, 20, 4)],
                              axis=1)]
            largest_df_static = df1[['Threshold', 'Total Hits Percent']].nlargest(n - 1, ['Total Hits Percent'])
            res = list(largest_df_static.to_records(index=False))

            joined_df = largest_df_static
            df_all_dynamic = pd.DataFrame()
            for insertion_algorithm_name in insertion_algorithm_name_array:
                df2 = df_dynamic[(df_dynamic['Experiment Name'] == experiment_names_dict[exp_name]) &
                                 (df_dynamic['Epoch'] == epoch) &
                                 (df_dynamic['In.'] == insertion_algorithm_name)]
                largest_df_dynamic = df2[['Total Hits Percent']].nlargest(1, ['Total Hits Percent'])
                largest_df_dynamic['Threshold'] = [insertion_algorithm_name]
                long_to_short = {'DTHillClimberBW_0.01_0.5': "HBW",
                                 'DTHillClimberUniqueFlows_0.01_0.5': 'HUF',
                                 'DynamicThresholdBW0.01_0.5': 'DBW',
                                 'DynamicThresholdUniqueFlow0.01_0.5': 'DUF'
                                 }
                res += [
                    (long_to_short[insertion_algorithm_name], max(list(largest_df_dynamic.to_records(index=False)))[0])]
                joined_df = pd.concat([joined_df, largest_df_dynamic])
                df_all_dynamic = pd.concat([df_all_dynamic, largest_df_dynamic])
            df_all_dynamic = pd.concat([df_all_dynamic, largest_df_static.nlargest(1, ['Total Hits Percent'])])
            df_all_dynamic['Experiment Name'] = [exp_name] * df_all_dynamic.shape[0]

            df_result_summary = pd.concat([df_result_summary, df_all_dynamic])
            res = sorted(res, key=lambda v: v[1])
            dynm_idx = []
            for insertion_algorithm_name in insertion_algorithm_name_array:
                dynm_idx.append([y[0] for y in res].index(long_to_short[insertion_algorithm_name]))
        # df_result_summary.to_csv('/home/itamar/PycharmProjects/CacheSimulator/Figures/1502/m400_s100/df_result_summary.csv')
        fig, ax = plt.subplots()
        data_x = list(range(len(res)))
        data_y = [y[1] for y in res]
        barlist = ax.bar(data_x, data_y, color='g')
        for idx in dynm_idx:
            barlist[idx].set_color('r')
        ax.set_ylabel("Total Hits %")
        ax.set_xlabel("Algorithm")
        ax.set_title("Top Algorithm (Cache hit) per trace {0}. Epoch {1}".format(exp_name, epoch))
        annot_array = [y[0] for y in res]
        for i in range(len(annot_array)):
            plt.annotate(str(annot_array[i]), xy=(data_x[i], data_y[i]), ha='center', va='bottom')
        ax.grid(True)
        ax.set_axisbelow(True)
        # plt.show()
        filename = 'classic_vs_dynamic_barplot_{0}_epoch{1}.png'.format(exp_name, epoch)
        base_dir = 'Figures/0603_400/m{0}_s{1}/'.format(main_cache_size, 500 - main_cache_size)
        ensure_dir(base_dir)
        joined_df.to_csv(base_dir + "{0}.csv".format(exp_name))
        fig.savefig(base_dir + filename, dpi=300)


def plot_hit_rate_different_cache_sizes_fixed_threshold(fixed_csv):
    df = pd.read_csv(fixed_csv)
    cache_configuration = np.unique(df[['Main Cache Size', 'Secondary Cache Size']])
    conf_arr = []
    for index, row in df.iterrows():
        conf_arr.append((row['Main Cache Size'], row['Secondary Cache Size']))
    experiment_name_array = np.unique(df['Experiment Name'])
    fig_result = {}

    for experiment_name in experiment_name_array:
        for th in np.unique(df['Threshold']):
            for mcs, scs in conf_arr:
                df_conf = df[(df['Main Cache Size'] == mcs) &
                             (df['Secondary Cache Size'] == scs) &
                             (df['Experiment Name'] == experiment_name) &
                             (df['Threshold'] == th)]
                fig_result[(mcs, scs)] = df_conf['Total Hits Percent'].max()

            fig, ax = plt.subplots()
            cache_conf_array = list(fig_result.keys())
            data_x = sorted(filter(lambda v: v[1] > 0, cache_conf_array)) + sorted(
                filter(lambda v: v[1] == 0, cache_conf_array))
            # data_x[4], data_x[5] = data_x[5], data_x[4]
            data_y = [fig_result[x] for x in data_x]
            barlist = ax.bar(list(map(str, data_x)), data_y, color='g')

            ax.set_ylabel("Total Hits %", fontsize=18)
            ax.set_xlabel("Cache Configuration (Main Cache Size, Secondary Cache Size)", fontsize=18)
            ax.set_title("Hit By Configuration -  Trace {0} Threshold: {1}".format(experiment_name.split('_')[0], th),
                         fontsize=20)
            annot_array = [fig_result[x] for x in data_x]
            data_x = list(map(str, data_x))
            for i in range(len(annot_array)):
                plt.annotate(str(annot_array[i]) + "%", xy=(data_x[i], data_y[i]), ha='center', va='bottom',
                             fontsize=12)
                # barlist[i].set_color(annot_array[i][1])

            ax.grid(True)
            ax.set_axisbelow(True)
            fig.set_size_inches(10, 5)
            plt.tight_layout()
            # plt.show()
            filename = 'cache_configuration_{0}_th{1}.png'.format(experiment_name.split('_')[0], th)
            base_dir = 'Figures/{0}/cache_conf_hitrate/'.format(fixed_csv.split('/')[-2])
            ensure_dir(base_dir)
            fig.savefig(base_dir + filename)
            print(base_dir + filename)


class TraceAnalysis:
    @staticmethod
    def summarize_trace_characteristics(json_path_array):
        name_hdr = 'Experiment Name'
        duration_hdr = 'Duration (sec)'
        util_avg_hdr = 'line_utilization_avg'
        util_std_hdr = 'line_utilization_std'
        uf_avg_hdr = 'unique_flow_count_avg'
        uf_std_hdr = 'unique_flow_count_std'
        burst_avg_hdr = 'burst_avg'
        burst_std_hdr = 'burst_std'
        headers = [name_hdr, duration_hdr, util_avg_hdr, util_std_hdr, uf_avg_hdr, uf_std_hdr, burst_avg_hdr,
                   burst_std_hdr]
        df_dict = {hdr: [] for hdr in headers}
        for json_path in json_path_array:
            with open(json_path, 'r') as f:
                data_plot = json.load(f)
                df_dict[name_hdr].append(json_path.split('/')[-2])
                # line_utilization
                x_data_array, y_data_array, y_data_avg, time_interval = data_plot['line_utilization']
                df_dict[duration_hdr].append(round(x_data_array[0][-1], 2))
                df_dict[util_avg_hdr].append(round(np.average(y_data_array[0]), 2))
                df_dict[util_std_hdr].append(round(np.std(y_data_array[0]), 2))

                # unique_flow_count
                unique_flow_count, time_interval = data_plot['unique_flow_count']
                df_dict[uf_avg_hdr].append(round(np.average(list(unique_flow_count.values())), 2))
                df_dict[uf_std_hdr].append(round(np.std(list(unique_flow_count.values())), 2))

                # plot_trace_burstiness
                x_data_array, y_data_array, x_label, y_label, title, line_description_array = data_plot[
                    'plot_trace_burstiness']
                df_dict[burst_avg_hdr].append(round(np.average(y_data_array[0]), 2))
                df_dict[burst_std_hdr].append(round(np.std(y_data_array[0]), 2))

        df = pd.DataFrame().from_dict(df_dict)
        df.to_csv('TGDriverCode/Traces/uniform_dst/trace_stat_summary.csv', index=False)

    @staticmethod
    def summarize_trace_characteristics_full_scheme(trace_base_dir):
        json_data_array = [(trace_base_dir + json_dir + '/plot_trace.json',
                            trace_base_dir + json_dir + '/packet_trace.json') for json_dir in
                           list(filter(lambda v: 'flows' in v, os.listdir(trace_base_dir)))]
        json_data_array = list(filter(lambda v: not os.path.exists(v[0]) and os.path.exists(v[1]), json_data_array))
        print("len(json_data_array) = {0}".format(len(json_data_array)))
        json_path_array = []
        for plot_trace_path, packet_trace_path in json_data_array:
            plot_data = PlotData(None,
                                 None,
                                 packet_trace_path)

            print("Processing: " + plot_trace_path)
            run_plot_data_preprocess(plot_data)
            plot_data.to_json(plot_trace_path)
            json_path_array.append(plot_trace_path)

        json_data_array = [trace_base_dir + json_dir + '/plot_trace.json' for json_dir in
                           list(filter(lambda v: 'flows' in v, os.listdir(trace_base_dir)))]
        print("len(json_data_array) = {0}".format(len(json_data_array)))
        TraceAnalysis.summarize_trace_characteristics(json_data_array)

    @staticmethod
    def add_clock_offset_to_packet_trace(packet_trace, clock_offset):
        for packet in packet_trace:
            packet[time_idx] += clock_offset

        return packet_trace

    @staticmethod
    def cut_trace(packet_trace_path, dst_trace_path, start_time, end_time):
        packet_trace = []
        start_idx = 0
        end_idx = None
        with open(packet_trace_path) as f:
            packet_trace = json.load(f)
            end_idx = len(packet_trace) - 1
            while start_idx < end_idx:
                if packet_trace[start_idx][time_idx] >= start_time:
                    print("packet_trace[start_idx][time_idx] >= start_time = " + str(
                        packet_trace[start_idx][time_idx] >= start_time))
                    break
                start_idx += 1
            while end_idx > start_idx:
                if packet_trace[end_idx][time_idx] <= end_time:
                    print(
                        "packet_trace[end_idx][time_idx] <= end_time = " + str(
                            packet_trace[end_idx][time_idx] <= end_time))
                    break
                end_idx -= 1
        offset = packet_trace[start_idx:end_idx][0][time_idx]
        print("=== pre offset ===")
        print(start_idx)
        print(end_idx)
        print(packet_trace[start_idx][time_idx])
        print(packet_trace[end_idx][time_idx])

        for packet in packet_trace[start_idx:end_idx]:
            packet[time_idx] -= offset

        print("=== post offset ===")
        print(packet_trace[start_idx][time_idx])
        print(packet_trace[end_idx][time_idx])
        print(len(packet_trace[start_idx:end_idx]))
        ensure_dir(dst_trace_path)
        with open(dst_trace_path, 'w') as f:
            json.dump(packet_trace[start_idx:end_idx], f)

    @staticmethod
    def cut_trace_by_percentage(src_trace_path, dst_trace_path, p_start=0.15, p_end=0.15):
        packet_trace = []
        start_idx = 0
        end_idx = None
        with open(src_trace_path) as f:
            packet_trace = json.load(f)
            start_time = packet_trace[int(len(packet_trace) * p_start)][time_idx]
            end_time = packet_trace[int(len(packet_trace) * (1 - p_end))][time_idx]
            print("src_trace_path = " + src_trace_path)
            print("dst_trace_path = " + dst_trace_path)
            print("start_time = " + str(start_time))
            print("end_time = " + str(end_time))
            end_idx = len(packet_trace) - 1
            while start_idx < end_idx:
                if packet_trace[start_idx][time_idx] >= start_time:
                    print("packet_trace[start_idx][time_idx] >= start_time = " + str(
                        packet_trace[start_idx][time_idx] >= start_time))
                    break
                start_idx += 1
            while end_idx > start_idx:
                if packet_trace[end_idx][time_idx] <= end_time:
                    print(
                        "packet_trace[end_idx][time_idx] <= end_time = " + str(
                            packet_trace[end_idx][time_idx] <= end_time))
                    break
                end_idx -= 1
        offset = packet_trace[start_idx:end_idx][0][time_idx]
        print("=== pre offset ===")
        print(start_idx)
        print(end_idx)
        print(packet_trace[start_idx][time_idx])
        print(packet_trace[end_idx][time_idx])

        for packet in packet_trace[start_idx:end_idx]:
            packet[time_idx] -= offset

        print("=== post offset ===")
        print(packet_trace[start_idx][time_idx])
        print(packet_trace[end_idx][time_idx])
        print(len(packet_trace[start_idx:end_idx]))
        ensure_dir(dst_trace_path)
        with open(dst_trace_path, 'w') as f:
            json.dump(packet_trace[start_idx:end_idx], f)

    @staticmethod
    def plot_data_to_csv(traces_path):
        experiment_name_array = os.listdir(traces_path)
        df = pd.DataFrame()
        for experiment_name in experiment_name_array:
            if not os.path.isfile(traces_path + experiment_name + '/plot_trace.json'):
                continue
            with open(traces_path + experiment_name + '/plot_trace.json') as f:
                experiment_data = json.load(f)
                row_data = {}
                row_data['Experiment Name'] = experiment_name
                x_data_array, y_data_array, y_data_avg, time_interval = experiment_data['line_utilization']
                row_data.update(
                    {'line_utilization_avg': np.average(y_data_array), 'line_utilization_std:': np.std(y_data_array)})
                x_data_array, y_data_array, x_label, y_label, title, line_description_array = experiment_data[
                    'plot_unique_and_overlap_rules']
                row_data.update(
                    {'unique rules avg': np.average(y_data_array[0]), 'unique rules std': np.std(y_data_array[0]),
                     'overlapping rules avg': np.average(y_data_array[1]),
                     'overlapping rules std': np.std(y_data_array[1]),
                     'non overlapping rules avg': np.average(y_data_array[2]),
                     'non overlapping rules std': np.std(y_data_array[1])})

                df = pd.concat([df, pd.DataFrame([row_data])])

        df.to_csv(traces_path + 'trace_stat_summary.csv')


class AnalyzeExperimentJson:
    @staticmethod
    def plot_dynamic_cache_configuration(clock_offset_json, experiment_json_path):
        # with open(clock_offset_json) as f:
        #     clock_offset_array = json.load(f)

        # vline_data = [t[1][0]/0.1 for t in clock_offset_array.items()]
        with open(experiment_json_path) as f:
            data = json.load(f)

        # for exp in data.keys():
        for exp in list(filter(lambda exp: 'FixedThreshold_8' in exp and '(0.015,1000)' in exp, list(data.keys()))):
            dcc_data = data[exp]["switch.controller.cache_configuration.logger.event_logger"]
            approx_epoch_value = dcc_data[EventType.controller_bw]
            epoch_value = dcc_data[EventType.switch_bw]
            cache_state = dcc_data[EventType.threshold]
            diff_value = dcc_data[EventType.big_cache_hit]

            fig, ax = plt.subplots(2, 1)
            ax[0].plot(list(range(len(diff_value))), diff_value, label="diff_value")
            ax[0].plot(list(range(len(diff_value))), [0] * len(diff_value))
            # ax[0].vlines(x=vline_data,
            #           ymin=min(diff_value),
            #           ymax=max(diff_value),
            #           colors='black',
            #           ls='--',
            #           lw=4)
            ax[0].legend()

            ax[1].plot(list(range(len(approx_epoch_value))), approx_epoch_value, label="approx_epoch_value")
            # ax[1].vlines(x=vline_data,
            #           ymin=min(approx_epoch_value),
            #           ymax=max(approx_epoch_value),
            #           colors='black',
            #           ls='--',
            #           lw=4)
            ax[1].legend()
            # ax[2].plot(list((range(len(epoch_value)))), epoch_value, label="epoch_value")
            # ax[2].legend()
            # ax[2].plot(list((range(len(cache_state)))), cache_state, label="cache_state")
            # ax[2].vlines(x=vline_data,
            #           ymin=min(cache_state),
            #           ymax=max(cache_state),
            #           colors='black',
            #           ls='--',
            #           lw=4)
            # ax[2].legend()

            fig.set_size_inches(10, 5)
            dir_name, file_name = experiment_json_path.split('/')[-2:]
            # file_name = file_name.split('.')[0].split('_')[-1] + '_' + clock_offset_json.split('/')[-2].split('_')[-1]
            file_name = exp
            ax[0].set_title(file_name)
            path_to_save = 'Figures/' + dir_name + '/' + file_name + '.jpg'
            print(path_to_save)
            # ensure_dir(path_to_save)
            ensure_dir(path_to_save)
            fig.savefig(path_to_save, dpi=300)

            # plt.show()

    @staticmethod
    def calc_ma(data, alpha=0.01):
        ma = [data[0]]
        for idx, d in enumerate(data[1:]):
            ma.append(ma[idx - 1] * (1 - alpha) + alpha * d)
        return ma

    @staticmethod
    def plot_diffrent_POV_mesures(json_path, clock_offset_json=None):
        step_size = 0.01
        step_size = 1
        with open(json_path) as f:
            data = json.load(f)

        if clock_offset_json:
            with open(clock_offset_json) as f:
                clock_offset_array = json.load(f)
                vline_data = [t[1][0] / 0.1 for t in clock_offset_array.items()]

        # for exp in data.keys():
        for exp in data.keys():
            # if exp != exp_key:
            #     continue
            # switch BW
            # switch UF

            switch_data = data[exp]["switch.logger.event_logger"]
            switch_bw = switch_data[EventType.switch_bw]
            switch_uf = switch_data[EventType.unique_flow]
            # Algorithm (controller) BW
            # Algorithm (controller) UF
            controller_bw = switch_data[EventType.controller_bw]
            controller_uf = switch_data[EventType.big_cache_hit]
            fig_title = " ".join(exp.split('_')[:2]) + ". Slow cache size: {0} Fast cache size: {1}".format(
                *[conf.split(",")[-1].strip(")") for conf in exp.split("|")[-2:]]) + " HitRate: " + data[exp]['str(switch)'].split(":")[3].split(',')[0] + "%"
            if len(controller_uf) != len(controller_bw):
                min_controller = min(len(controller_uf), len(controller_bw))
                controller_bw = controller_bw[:min_controller]
                controller_uf = controller_uf[:min_controller]

            fig, axs = plt.subplots(3, 2, constrained_layout=True)
            fig.suptitle(fig_title, fontsize=title_font_size)
            axs[0, 0].plot(np.arange(len(switch_bw) * step_size, step=step_size), switch_bw, label="RAW")
            axs[0, 0].plot(np.arange(len(switch_bw) * step_size, step=step_size), AnalyzeExperimentJson.calc_ma(switch_bw),
                           label="MA")
            axs[0, 0].set_title('Switch BW', fontsize=title_font_size)
            axs[0, 0].set_xlabel('Time [sec]', fontsize=xy_tick_font_size)
            axs[0, 0].set_ylabel('BW [count]', fontsize=xy_tick_font_size)
            axs[0, 0].tick_params(labelsize=xy_tick_font_size)
            axs[0, 0].legend(loc='upper right', prop={'size': 24})

            axs[1, 0].plot(np.arange(len(switch_uf) * step_size, step=step_size), switch_uf, label="RAW")
            axs[1, 0].plot(np.arange(len(switch_uf) * step_size, step=step_size), AnalyzeExperimentJson.calc_ma(switch_uf),
                           label="MA")
            axs[1, 0].set_title('Switch Unique Flows', fontsize=title_font_size)
            axs[1, 0].set_xlabel('Time [sec]', fontsize=xy_tick_font_size)
            axs[1, 0].set_ylabel('Unique Flows [count]', fontsize=xy_tick_font_size)
            axs[1, 0].tick_params(labelsize=xy_tick_font_size)
            axs[1, 0].legend(loc='upper right', prop={'size': 24})

            burst_data = [bw / uf if uf != 0 else 0 for bw, uf in zip(switch_bw, switch_uf)]
            axs[2, 0].plot(np.arange(len(burst_data) * step_size, step=step_size), burst_data, label="RAW")
            axs[2, 0].plot(np.arange(len(burst_data) * step_size, step=step_size), AnalyzeExperimentJson.calc_ma(burst_data),
                           label="MA")
            axs[2, 0].set_title('BW/UniqueFlows From Switch', fontsize=title_font_size)
            axs[2, 0].set_xlabel('Time [sec]', fontsize=xy_tick_font_size)
            axs[2, 0].set_ylabel('Burstiness', fontsize=xy_tick_font_size)
            axs[2, 0].tick_params(labelsize=xy_tick_font_size)
            axs[2, 0].legend(loc='upper right', prop={'size': 24})
            axs[2, 0].set_yscale('log')


            axs[0, 1].plot(np.arange(len(controller_bw) * step_size, step=step_size), controller_bw, label="RAW")
            axs[0, 1].plot(np.arange(len(controller_bw) * step_size, step=step_size), AnalyzeExperimentJson.calc_ma(controller_bw),label="MA")

            axs[0, 1].set_title('Controller BW', fontsize=title_font_size)
            axs[0, 1].set_xlabel('Time [sec]', fontsize=xy_tick_font_size)
            axs[0, 1].set_ylabel('BW [count]', fontsize=xy_tick_font_size)
            axs[0, 1].tick_params(labelsize=xy_tick_font_size)
            axs[0, 1].legend(loc='upper right', prop={'size': 24})

            axs[1, 1].plot(np.arange(len(controller_uf) * step_size, step=step_size), controller_uf, label="RAW")
            axs[1, 1].plot(np.arange(len(controller_uf) * step_size, step=step_size), AnalyzeExperimentJson.calc_ma(controller_uf),label="MA")
            axs[1, 1].set_title('Controller Unique Flows', fontsize=title_font_size)
            axs[1, 1].set_xlabel('Time [sec]', fontsize=xy_tick_font_size)
            axs[1, 1].set_ylabel('Unique Flows [count]', fontsize=xy_tick_font_size)
            axs[1, 1].tick_params(labelsize=xy_tick_font_size)
            axs[1, 1].legend(loc='upper right', prop={'size': 24})

            cntl_burst_data = [bw / uf if uf != 0 else 0 for bw, uf in zip(controller_bw, controller_uf)]
            axs[2, 1].plot(np.arange(len(controller_uf) * step_size, step=step_size),cntl_burst_data, label="RAW")
            axs[2, 1].plot(np.arange(len(controller_uf) * step_size, step=step_size),AnalyzeExperimentJson.calc_ma(cntl_burst_data), label="MA")
            axs[2, 1].set_title('BW/UniqueFlows from controller', fontsize=title_font_size)
            axs[2, 1].set_xlabel('Time [sec]', fontsize=xy_tick_font_size)
            axs[2, 1].set_ylabel('Burstiness', fontsize=xy_tick_font_size)
            axs[2, 1].set_yscale('log')
            axs[2, 1].tick_params(labelsize=xy_tick_font_size)
            axs[2, 1].legend(loc='upper right', prop={'size': 24})

            fig.set_size_inches(42, 24)

            base_dir = "Figures/{0}".format("/".join(json_path.split('/')[-3:-1]))
            figname = "_".join(exp.split('_')[:2]) + "_({0},{1}).jpg".format(
                *[conf.split(",")[-1].strip(")") for conf in exp.split("|")[-2:]])
            file_path = base_dir + '/' + figname
            ensure_dir(file_path)
            print(file_path)
            fig.savefig(file_path)


def main():
    src_base_dir = "/home/user46/CacheSimulator/SimulatorTrace/"
    dst_base_dir = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/"

    prefix = "0304_chain"
    prefix = "2903/"
    prefix = "0404/"
    prefix = "0504/"
    # prefix = "0604_joined/"
    # prefix = "0704_joined/"
    # prefix = "1004_joined/"
    prefix = "2504_FB"
    prefix = "0205/"
    prefix = "DynamicCacheAlgorithms0810/"

    input_path_array = [
        prefix + "/dynamic_threshold",
        prefix + "/fixed_threshold",
    ]

    dynamic_csv = dst_base_dir + input_path_array[0] + "/uniform_dst/complete_summary.csv"
    fixed_csv = dst_base_dir + input_path_array[1] + "/uniform_dst/complete_summary.csv"

    # CompareCompleteSummary.create_complete_summary_csv(dst_base_dir + prefix)
    # path = dst_base_dir + input_path_array[1] + "/uniform_dst"
    # CompareCompleteSummary.create_complete_summary_csv(dst_base_dir + prefix)
    # complete_summary = "{0}/complete_summary.csv".format(path)
    # CompareCompleteSummary.compare_dynamic_as_bar_static_as_dot(complete_summary)
    # CompareCompleteSummary.find_best_dynamic_threshold_algorithm(complete_summary)
    # CompareCompleteSummary.compare_best_static_per_configuration(complete_summary)
    # CompareCompleteSummary.configuration_heatmap(complete_summary, 'Figures/{0}/cache_conf/'.format(prefix))

    # fixed_work_dir = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/0504/fixed_threshold/uniform_dst/"
    # trace_dir = "/home/itamar/PycharmProjects/CacheSimulator/TGDriverCode/Traces/"
    # exp_name = "FB_Hadoop_Inter_Rack_FlowCDF_n_flows50000_deficit_param1000_flow_per_sec80_flowlet_per_sec1"
    # quanta = 1.0
    # AnalyzeBestFixedThresholdPerQuanta.plot_analyze_best_fixed_per_quanta(fixed_work_dir, trace_dir, exp_name, quanta)

    # cs1 = '/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/0105/complete_summary.csv'
    # cs2 = '/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/{0}complete_summary.csv'.format(prefix)
    # CompareCompleteSummary.compare_two_complete_summaries(cs1, cs2)

    exp = ["100_AVGburstDCC.json",
           "100_BandwidthDCC.json",
           "100_NormalUniqueFlowsDCC.json",
           "100_UniqueFlowsDCC.json"]

    # clock_offset_json = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/join_trace_static_websearch/trace_times.json"

    # clock_offset_json = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/joined_trace_static_FB/trace_times.json"

    # for exp_name in exp:
    #     path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/join_trace_static_websearch/{0}".format(exp_name)
    #     plot_dynamic_cache_configuration(clock_offset_json, path)

    caida_path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/caida_trace/"
    # SimulatorIO.csv_from_json_folder(caida_path)

    # plot_hit_rate_different_cache_sizes_fixed_threshold(caida_path + 'all_experiments_static.csv')

    # json_path = '/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1505/caida_trace/caida_json.json'
    # json_path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1605/caida_trace_srcdst/caida_json.json"
    # json_path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1605/caida_trace_srcdst/"
    FB_json_path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1605/FB/experiment_result.json"
    websearch_json_path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1605/websearch/experiment_result.json"
    caida_json_path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1605/caida_trace_srcdst/caida_json.json"

    path = "/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/2405/fb_clusterA_full_10M/FixedThreshold_2_0.01_0.5|Random|StaticCacheConfiguration|(0.015,300000)|0.005,0).json"

    AnalyzeExperimentJson.plot_diffrent_POV_mesures(path)
    # AnalyzeExperimentJson.plot_diffrent_POV_mesures(FB_json_path)
    # AnalyzeExperimentJson.plot_diffrent_POV_mesures(caida_json_path)

    # SimulatorIO.csv_from_json_folder("/".join(caida_json_path.split('/')[:-1]) + '/')
    # plot_hit_rate_different_cache_sizes_fixed_threshold("/home/itamar/PycharmProjects/CacheSimulator/SimulatorTrace/1605/websearch/complete_summary.csv")


if __name__ == "__main__":
    main()
