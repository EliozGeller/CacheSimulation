#!/usr/bin/env python
import json
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import colorsys
import os
from SimulatorIO import SimulatorIO
from TGDriverCode.PlotTrace import run_plot_trace
from TimeSeriesLogger import EventType
from TGDriverCode.PlotTrace import figs_to_save, PlotData

xy_label_font_size = 48
title_font_size = 48
xy_tick_font_size = 36


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


xy_label_font_size = 48
title_font_size = 48
xy_tick_font_size = 36


class ExperimentConfig:
    def __init__(self, cache_size, delay):
        self.cache_size = cache_size
        self.delay = delay


class SingleTraceExperiment:
    def __init__(self, work_dir, all_experiments_filename='all_experiments.csv'):
        self.work_dir = work_dir
        self.all_experiments = pd.read_csv(work_dir + all_experiments_filename)

    def get_result(self, experiment_configuration):
        tmp_df = self.all_experiments[(self.all_experiments['Cache Size'] == experiment_configuration.cache_size) &
                                      (self.all_experiments['Controller Delay'] == experiment_configuration.delay)]
        return int(
            np.average(tmp_df[(tmp_df['Total Hits Percent'] == tmp_df['Total Hits Percent'].max())]['Threshold']))


class JoinedTraceExperiment:
    def __init__(self,
                 static_dynamic_compare_csv_path,
                 joined_dynamic_work_dir,
                 joined_fixed_work_dir,
                 trace_times='trace_times.json'):
        """
        :param static_dynamic_compare_csv_path: csv that compare between the fixed and the dynamic experiments
        :param joined_dynamic_work_dir: directory with jsons of the dynamic threshold data over joined trace
        :param joined_fixed_work_dir: directory with jsons of the fixed threshold data over joined trace
        :param fixed_work_dir: directory of directories with jsons of the fixed threshold over the separated trace
        """
        self.static_dynamic_compare_df = pd.read_csv(static_dynamic_compare_csv_path)
        self.joined_dynamic_work_dir = joined_dynamic_work_dir
        self.joined_fixed_work_dir = joined_fixed_work_dir
        with open(joined_dynamic_work_dir + trace_times) as f:
            self.trace_times = json.load(f)

    def static_vs_dynamic_per_experiment(self):
        df = self.static_dynamic_compare_df[
            ['In.', 'Threshold', 'Increase Method', 'Decrease Method', 'Controller Delay',
             'Cache Size', 'Total Hits Percent']]
        cache_size_array = np.unique(df['Cache Size'])
        controller_delay_array = np.unique(df['Controller Delay'])
        plot_data = {}
        y_data_array = []
        for controller_delay in controller_delay_array:
            y_dynamic_threshold = []
            dynamic_threshold_label = []
            y_fixed_threshold = []
            fixed_threshold_label = []
            for cache_size in cache_size_array:
                configuration_df = df[(df['Cache Size'] == cache_size) &
                                      (df['Controller Delay'] == controller_delay)]

                dynamic_threshold_df = configuration_df[configuration_df['In.'] == 'DynamicThreshold_1_0.01_0.5']
                y_fixed_threshold_df = configuration_df[configuration_df['In.'] == 'FixedThreshold']

                y_fixed_threshold.append(max(y_fixed_threshold_df['Total Hits Percent']))
                y_dynamic_threshold.append(max(dynamic_threshold_df['Total Hits Percent']))

                fixed_threshold_label.append(int(max(y_fixed_threshold_df['Threshold'])))
                dynamic_label = ','.join(dynamic_threshold_df.sort_values('Increase Method').sort_values(
                    'Decrease Method').iloc[-1][['Increase Method', 'Decrease Method']])
                dynamic_threshold_label.append(dynamic_label)
                y_data_array = y_data_array + [y_dynamic_threshold, y_fixed_threshold]
            plot_data[controller_delay] = [y_dynamic_threshold,
                                           dynamic_threshold_label,
                                           y_fixed_threshold,
                                           fixed_threshold_label]
        return plot_data


class PlotCacheSimulator:
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
    def plot_multiple_lines(x_data_array, y_data_array, x_label, y_label, title, line_description_array,
                            experiment_title=None, vline_data_x=None):
        fig, ax = plt.subplots()
        for x_data, y_data, line_descp in zip(x_data_array, y_data_array, line_description_array):
            ax.plot(x_data, y_data, label=line_descp)

        if experiment_title:
            fig.text(0.5, 0.98, experiment_title, ha="center", fontsize=24,
                     bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5})

        if vline_data_x:
            y_high = max([max(y_data) for y_data in y_data_array])
            ax.vlines(x=vline_data_x,
                      ymin=[0] * len(vline_data_x),
                      ymax=[y_high] * len(vline_data_x),
                      colors='black',
                      ls='--',
                      lw=4,
                      label='Threshold Change Indicator')

        ax.legend(loc='upper right', prop={'size': 24})
        ax.set_xlabel(x_label, fontsize=xy_label_font_size)
        ax.set_ylabel(y_label, fontsize=xy_label_font_size)
        ax.set_title(title, fontsize=title_font_size)
        ax.tick_params(labelsize=xy_tick_font_size)
        # ax.set_yscale('log')
        ax.grid(True)
        ax.legend(prop={'size': 24})

        return fig

    @staticmethod
    def plot_multiple_plots_multiple_lines(ax_x_data_array, ax_y_data_array, ax_x_label, ax_y_label, ax_title,
                                           ax_line_description_array):
        fig, axes = plt.subplots(int((np.ceil(len(ax_x_data_array) / 2))), 2)
        i = 0
        for row in axes:
            for ax in row:
                for x_data, y_data, line_descp in zip(ax_x_data_array[i], ax_y_data_array[i],
                                                      ax_line_description_array[i]):
                    ax.scatter(x_data, y_data, label=line_descp)
                    ax.plot(x_data, y_data, '--')
                ax.set_xlabel(ax_x_label[i])
                ax.set_ylabel(ax_y_label[i])
                ax.set_title(ax_title[i])
                ax.legend()
                i += 1
                if i >= len(ax_x_data_array):
                    fig.tight_layout()
                    return

    @staticmethod
    def plot_fixed_threshold_experiment_from_json(json_path, experiment_names=None):
        with open(json_path) as f:
            logger_dict = json.load(f)

        experiment_names = logger_dict.keys() if experiment_names is None else experiment_names
        for experiment_title in experiment_names:
            # switch bandwidth vs controller bandwidth
            event_logger, controller_event_logger, time_slice, switch_str, insertion_algo_data, \
            eviction_algo_data, rules_statistics = logger_dict[experiment_title]
            event_logger = {int(event): event_logger[event] for event in event_logger}
            time_slice = {int(ts): time_slice[ts] for ts in time_slice}

            line_rate = 100000

            x_data_array = [range(len(event_logger[EventType.switch_bw])),
                            range(len(event_logger[EventType.controller_bw]))]
            y_data_array = [
                [(v * time_slice[EventType.switch_bw]) / line_rate for v in event_logger[EventType.switch_bw]],
                [(v * time_slice[EventType.controller_bw]) / line_rate for v in event_logger[EventType.controller_bw]]]
            x_label = "Time - slice: " + str(time_slice[EventType.switch_bw])
            y_label = "Bandwidth"
            title = "Switch VS Controller bandwidth over time"
            line_description_array = ["Switch BW", "Controller BW"]
            fig = PlotCacheSimulator.plot_multiple_lines(x_data_array, y_data_array, x_label, y_label, title,
                                                         line_description_array)
            fig.text(0.5, 0.01, switch_str, ha="center", fontsize=24,
                     bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5})

            file_path = 'Figures/' + json_path.split('/')[-2] + '/'
            ensure_dir(file_path)
            print(file_path)
            fig.set_size_inches(42, 24)
            fig.savefig(file_path + experiment_title + '.jpg')

    @staticmethod
    def legend_without_duplicate_labels(ax):
        handles, labels = ax.get_legend_handles_labels()
        unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
        ax.legend(*zip(*unique), prop={'size': 24})

    @staticmethod
    def plot_static_vs_dynamic_all_experiments(joined_experiment):
        """"
        :param joined_experiment:  JoinedExperiment object
        :return:
        """
        plot_data = joined_experiment.static_vs_dynamic_per_experiment()
        cache_size_array = np.unique(joined_experiment.static_dynamic_compare_df['Cache Size'])
        x_data = [str(c_sz) for c_sz in cache_size_array]
        i = 0
        markes = ['s', 'o']
        colors = PlotCacheSimulator.get_colors(20)
        np.random.shuffle(colors)
        dynamic_label_to_color = {}
        fixed_label_to_color = {}

        count = 0
        for controller_delay in plot_data:
            y_dynamic, dynamic_label, y_fixed, fixed_label = plot_data[controller_delay]
            for dl in np.unique(dynamic_label):
                dynamic_label_to_color[dl] = colors[count]
                count += 1
            for dl in np.unique(fixed_label):
                fixed_label_to_color[dl] = colors[count]
                count += 1

        fig, axs = plt.subplots(2, constrained_layout=True)
        fig.suptitle('Dynamic vs. Static threshold over Cache Size',
                     fontsize=title_font_size)

        locator = [(1, 0), (0, -2), (0, -2)]
        for controller_delay in plot_data:
            y_dynamic, dynamic_label, y_fixed, fixed_label = plot_data[controller_delay]
            for j in range(len(dynamic_label)):
                axs[i].scatter(x_data[j], y_dynamic[j], label='Dynamic: ' + dynamic_label[j], marker=markes[1], s=500,
                               color=dynamic_label_to_color[dynamic_label[j]])
                # axs[i].annotate('Dynamic: ' + dynamic_label[j], xy=(str(int(x_data[j]) + locator[j][0]), int(y_dynamic[j]) + locator[j][1]))

            for j in range(len(fixed_label)):
                axs[i].scatter(x_data[j], y_fixed[j], label='Fixed Threshold: ' + str(fixed_label[j]), marker=markes[0],
                               s=500, color=fixed_label_to_color[fixed_label[j]])

            axs[i].plot(x_data, y_dynamic, '--', color='k')
            axs[i].plot(x_data, y_fixed, '--', color='k')

            axs[i].legend(loc='upper right', prop={'size': 24})
            axs[i].set_xlabel('Cache Size', fontsize=xy_label_font_size)
            axs[i].set_ylabel('Total Hits Percent (%)', fontsize=xy_label_font_size)
            axs[i].set_title('Delay:' + str(controller_delay), fontsize=xy_label_font_size)
            axs[i].tick_params(labelsize=xy_tick_font_size)

            i += 1

        PlotCacheSimulator.legend_without_duplicate_labels(axs[0])
        PlotCacheSimulator.legend_without_duplicate_labels(axs[1])

        # fig.tight_layout()
        return fig

    @staticmethod
    def compare_joined_dynamic_single_best(joined_experiment, experiment_configuration, single_trace):
        ## Experiment Data preprocesss

        df = joined_experiment.static_dynamic_compare_df
        data_row = df[(df['Cache Size'] == experiment_configuration.cache_size) & (
                df['Controller Delay'] == experiment_configuration.delay) & (df['In.'] != 'FixedThreshold')].to_dict(
            'records')[0]
        json_name = SimulatorIO.dynamic_experiment_row_data_to_json(data_row)

        with open(joined_experiment.joined_dynamic_work_dir + json_name) as f:
            experiment_data = json.load(f)

        # extract the desired delay configuration from json
        experiment_key = list(filter(lambda name: str(experiment_configuration.delay)
                                                  in name.split(',')[-2], [x[0] for x in
                                                                           list(experiment_data.items())]))[0]
        experiment_data = experiment_data[experiment_key]
        return PlotCacheSimulator.compare_single_joined_dynamic_experiment_multple_traces(experiment_configuration,
                                                                                          joined_experiment,
                                                                                          experiment_data,
                                                                                          single_trace)

    @staticmethod
    def compare_single_joined_dynamic_experiment_multple_traces(experiment_configuration,
                                                                joined_experiment,
                                                                experiment_data,
                                                                single_trace,
                                                                increase_method_str=None,
                                                                decrease_method_str=None
                                                                ):
        event_logger, controller_event_logger, time_slice_data, switch_str, insertion_algo_data, \
        eviction_algo_data = experiment_data
        increase_method_str = increase_method_str if increase_method_str else insertion_algo_data['Increase Method']
        decrease_method_str = decrease_method_str if decrease_method_str else insertion_algo_data['Decrease Method']

        df = joined_experiment.static_dynamic_compare_df
        best_fixed_joined_trace = int(df[(df['Cache Size'] == experiment_configuration.cache_size) &
                                         (df['Controller Delay'] == experiment_configuration.delay) &
                                         (df['In.'] == 'FixedThreshold')]['Threshold'])

        best_fixed_threshold_per_trace = [single_trace[trace_name].get_result(experiment_configuration) for trace_name
                                          in joined_experiment.trace_times.keys()]

        trace_times = list(joined_experiment.trace_times.values())

        time_slice = time_slice_data[str(EventType.switch_bw)]  # assuming the same time slice for all metrics
        line_rate = 100000
        ## Plot Data preprocess
        dynamic_threshold = controller_event_logger[str(EventType.threshold)]
        controller_bw = [(100 * d) / (line_rate * time_slice) for d in event_logger[str(EventType.controller_bw)]]
        switch_bw = [(100 * d) / (line_rate * time_slice) for d in event_logger[str(EventType.switch_bw)]]
        data_y = []
        vline_x_data = [0]
        for t, ft in zip(trace_times, best_fixed_threshold_per_trace):
            t_s, t_e = t
            data_y = data_y + [ft] * (int(np.around(t_e - t_s) / time_slice))
            vline_x_data = vline_x_data + [int(np.around(t_e - t_s) / time_slice) + vline_x_data[-1]]

        ## Plot Data
        fig, ax = plt.subplots(2, 1, constrained_layout=True)
        fig.suptitle('Controller Delay :' + str(experiment_configuration.delay) +
                     ' Cache Size:' + str(experiment_configuration.cache_size), fontsize=xy_label_font_size)
        ax[0].set_title("Controller and Switch (Total) BW - Line Utilization (%)", fontsize=xy_label_font_size)
        ax[0].plot(range(len(controller_bw)), controller_bw, label="Controller BW (%)")
        ax[0].plot(range(len(switch_bw)), switch_bw, label="Total (Switch) BW (%)")
        ax[0].set_ylabel("Bandwidth Percent (%)", fontsize=xy_label_font_size)
        ax[0].set_xlabel("Time - Time slice : " + str(time_slice), fontsize=xy_label_font_size)
        ax[0].vlines(x=vline_x_data[1:-1],
                     ymin=[0] * len(vline_x_data[1:-1]),
                     ymax=[100] * len(vline_x_data[1:-1]),
                     colors='black',
                     ls='--',
                     lw=4,
                     label='Trace Change Indicator')
        ax[1].set_title(
            'DynamicThreshold: Increase Method: ' + increase_method_str +
            ' Decrease Method: ' + decrease_method_str + '\n' + " FixedThreshold: " +
            " ".join(["T" + str(i) + "=" + str(ft) for i, ft in
                      zip(range(len(best_fixed_threshold_per_trace)),
                          best_fixed_threshold_per_trace)]), fontsize=xy_label_font_size)
        ax[1].plot(range(len(data_y)), data_y, color="r", label="Best Fixed Threshold per trace", linewidth=4)
        ax[1].plot(range(len(data_y)),
                   # '--',
                   [best_fixed_joined_trace] * (len(data_y)),
                   label="Best Fixed Threshold Joined Trace",
                   linewidth=2)
        ax[1].plot(range(len(dynamic_threshold)), dynamic_threshold, color="g", label="Dynamic Threshold")
        ax[1].set_ylabel("Threshold", fontsize=xy_label_font_size)
        ax[1].set_xlabel("Time - Time slice : " + str(time_slice), fontsize=xy_label_font_size)
        max_y = max(max(dynamic_threshold), max(best_fixed_threshold_per_trace), best_fixed_joined_trace)
        ax[1].vlines(x=vline_x_data[1:-1],
                     ymin=[0] * len(vline_x_data[1:-1]),
                     ymax=[max_y] * len(vline_x_data[1:-1]),
                     colors='black',
                     ls='--',
                     lw=4,
                     label='Trace Change Indicator')

        ax[0].legend(prop={'size': 24})
        ax[1].legend(prop={'size': 24})

        ax[0].tick_params(labelsize=xy_tick_font_size)
        ax[1].tick_params(labelsize=xy_tick_font_size)

        return fig

    @staticmethod
    def compare_joined_dynamic_all_best(joined_experiment, single_trace_dict, file_path):
        cache_size_array = [100, 300, 500]
        controller_delay_array = [0.001, 0.1]
        for cache_size in cache_size_array:
            for controller_delay in controller_delay_array:
                fig = PlotCacheSimulator.compare_joined_dynamic_single_best(joined_experiment,
                                                                            ExperimentConfig(
                                                                                cache_size=cache_size,
                                                                                delay=controller_delay),
                                                                            single_trace_dict)
                fig.set_size_inches(42, 24)
                ensure_dir(file_path)
                print(file_path + str(cache_size) + '_' + str(controller_delay) + '.jpg')
                fig.savefig(file_path + str(cache_size) + '_' + str(controller_delay) + '.jpg')

    @staticmethod
    def plot_fixed_threshold_over_delay(csv_path):
        df = pd.read_csv(csv_path)
        cache_size_array = np.unique(df['Cache Size'])
        delay_array = np.unique(df['Controller Delay'])
        eviction_algorithms = np.unique(df['Evic.'])
        eviction_algorithm = 'Random'
        x_data_array = []
        y_data_array = []
        ax_x_label = []
        ax_y_label = []
        ax_title = []
        ax_line_description_array = []
        for cache_size in cache_size_array:
            x_data = []
            y_data = []
            for delay in delay_array:
                df_to_plot = df.loc[(df['Cache Size'] == cache_size) &
                                    (df['Controller Delay'] == delay) &
                                    (df['Evic.'] == eviction_algorithm)]

                data = sorted([(x, y) for x, y in zip(df_to_plot['Threshold'], df_to_plot['Total Misses Percent'])],
                              key=lambda x: x[0])
                x_data.append([str(x[0]) for x in data])
                y_data.append([y[1] for y in data])
            x_data_array.append(x_data)
            y_data_array.append(y_data)
            ax_title.append("Cache Size: " + str(cache_size))
            ax_x_label.append("Threshold")
            ax_y_label.append("Miss Rate %")
            ax_line_description_array.append(delay_array)

        PlotCacheSimulator.plot_multiple_plots_multiple_lines(x_data_array, y_data_array, ax_x_label,
                                                              ax_y_label,
                                                              ax_title, ax_line_description_array)
        plt.show()

    @staticmethod
    def plot_analyze_best_fixed_per_quanta(data_x_array, data_y_array, x_label_array, y_label_array, title_array,
                                           line_description_array,
                                           vline_data_x=None):
        fig, axes = plt.subplots(len(data_y_array), 1, constrained_layout=True)
        for i, ax in enumerate(axes):
            data_y, avg_y = data_y_array[i]
            data_x, avg_x = data_x_array[i]
            ax.plot(data_x, data_y, linewidth=3, label=line_description_array[i][0])
            if avg_y:
                ax.plot(avg_x, avg_y, linewidth=3, label=line_description_array[i][1])
            y_high = max(data_y)
            y_low = min(data_y)
            ax.vlines(x=vline_data_x,
                      ymin=[y_low] * len(vline_data_x),
                      ymax=[y_high] * len(vline_data_x),
                      colors='black',
                      ls='--',
                      lw=1,
                      label='Threshold Change Indicator')
            ax.set_xlabel(x_label_array[i], fontsize=xy_label_font_size)
            ax.set_ylabel(y_label_array[i], fontsize=xy_label_font_size)
            ax.set_title(title_array[i],  fontsize=title_font_size)
            ax.tick_params(labelsize=xy_tick_font_size)
            ax.legend(loc='upper right', prop={'size': 24})
            ax.grid(True)
        return fig

    @staticmethod
    def plot_hypothesis_bar(hypothesis_array, data_x, title):
        x_axis = []
        colors = ['green', 'orange', 'tab:blue', 'tab:red', 'cyan']
        fig, ax = plt.subplots()
        for idx, h in enumerate(hypothesis_array):
            s_axis = np.linspace(-1 / len(h), 1 / len(h), len(h))
            s_axis += idx
            data_y = sorted(h.items(), key=lambda v: v[0])
            x_axis += list(s_axis)
            bar_width = np.abs(s_axis[-1]) - np.abs(s_axis[-2])
            barlist = ax.bar(list(s_axis), [y[1] for y in data_y],
                             bar_width - 0.05 * bar_width,
                             edgecolor='black')
            for i in range(len(data_y)):
                barlist[i].set_color(colors[i])

            for x, y_tup in zip(s_axis, data_y):
                ax.annotate(y_tup[0], xy=(x, y_tup[1]), ha='center', va='bottom', fontsize=xy_label_font_size/2)

        ax.set_xticks([0, 1, 2], data_x)
        ax.tick_params(labelsize=xy_tick_font_size)
        ax.set_ylabel("Count (%)", fontsize=xy_label_font_size)
        ax.set_title(title, fontsize=title_font_size)
        ax.legend()
        ax.grid(True)

        return fig


def main():
    experiment_names_dict = {
        'B1': 'n_flows100000_deficit_param100_flow_per_sec1000_flowlet_per_sec1000',
        # 87.5334104627767	113.071500503525
        'NB1': 'n_flows100000_deficit_param1000_flow_per_sec1000_flowlet_per_sec1',
        # 74.0461096829477	270.866666666667
        'B2': 'n_flows100000_deficit_param10_flow_per_sec1000_flowlet_per_sec1000',
        # 86.2393313373254	105.955044955045
        'NB2': 'n_flows100000_deficit_param100_flow_per_sec1000_flowlet_per_sec1'}



if __name__ == "__main__":
    main()
