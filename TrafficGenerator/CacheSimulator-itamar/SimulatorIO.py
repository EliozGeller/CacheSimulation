import json
import os
from Switch import Switch
from TimeSeriesLogger import *
import pandas as pd
import re

columns_by_order = [
    'In.',
    'In. Aging Period',
    'In. Aging Factor',
    'Threshold',
    'Epoch',
    # 'Trend Factor',
    'Increase Method',
    'Decrease Method',
    'Evic.',
    # 'Param',
    'Cache Conf',
    'Cache Conf Epoch',
    'Main Cache Delay',
    'Main Cache Size',
    'Secondary Cache Delay',
    'Secondary Cache Size',
    'Total Accesses',
    'Total Hits Count',
    'Total Hits Percent',
    'Total Misses',
    'Total Misses Percent',
]


class CombineCSV:
    def __init__(self):
        self.df = pd.DataFrame()

    def add_df(self, csv_path, experiment_name):
        df = pd.read_csv(csv_path)
        df['Experiment Name'] = [experiment_name] * int(df.shape[0])
        self.df = pd.concat([self.df, df])

    def save_new_csv(self, path_to_save):
        self.df.to_csv(path_to_save)


class SimulatorIO:
    @staticmethod
    def experiment_to_json(switch_array, output_json_path):
        out_data = {}
        for switch in switch_array:
            experiment_key = SimulatorIO.create_experiment_key(switch)
            out_data[experiment_key] = {
                "switch.logger.event_logger": switch.logger.event_logger,
                "insertion_algorithm.logger.event_logger": switch.controller.insertion_algorithm.logger.event_logger,
                "switch.logger.time_slice": switch.logger.time_slice,
                "str(switch)": str(switch),
                "switch.controller.insertion_algorithm.column_data": switch.controller.insertion_algorithm.column_data,
                "switch.cache.eviction_algorithm.column_data": switch.cache.eviction_algorithm.column_data,
                "switch.controller.cache_configuration.column_data": switch.controller.cache_configuration.column_data,
                "switch.controller.cache_configuration.logger.event_logger": switch.controller.cache_configuration.logger.event_logger
            }

        with open(output_json_path, 'w') as f:
            json.dump(out_data, f)

    @staticmethod
    def create_experiment_key(switch):
        insertion_algorithm_name = switch.controller.insertion_algorithm.name
        eviction_algorithm_name = switch.cache.eviction_algorithm.name
        cache_configuration_algo_name = switch.controller.cache_configuration.name
        experiment_key = insertion_algorithm_name + "|" + eviction_algorithm_name + "|" + \
                         cache_configuration_algo_name + "|(" + str(
            switch.cache.insertion_delay['slow_cache']) + "," + str(
            switch.cache.cache_size['slow_cache']) + ')|' + str(
            switch.cache.insertion_delay['fast_cache']) + ',' + str(switch.cache.cache_size['fast_cache']) + ')'
        return experiment_key

    @staticmethod
    def csv_from_json_folder(dirpath):
        json_path_list = list(filter(lambda s: "json" in s and 'trace_times.json' not in s, os.listdir(dirpath)))
        df_array = []
        for json_path in json_path_list:
            with open(dirpath + json_path) as f:
                df = SimulatorIO.json_to_dataframe(json.load(f))
                df_array.append(df)

        result_df = pd.concat(df_array)[columns_by_order]
        result_df.to_csv(dirpath + "all_experiments.csv", index=False)

    @staticmethod
    def create_insert_key(target_dict, key, value):
        if key in target_dict:
            target_dict[key].append(value)
        else:
            target_dict[key] = [value]

    @staticmethod
    def json_to_dataframe(experiment_data):
        data_out = {}
        for experiment in experiment_data:
            slow_cache, fast_cache = experiment.split("|")[-2:]
            slow_cache_delay, slow_cache_size = [re.sub(r'[()]', '', val).strip() for val in slow_cache.split(',')]
            fast_cache_delay, fast_cache_size = [re.sub(r'[()]', '', val).strip() for val in fast_cache.split(',')]

            in_algo_col_data = experiment_data[experiment]['switch.controller.insertion_algorithm.column_data']
            evic_algo_col_data = experiment_data[experiment]['switch.cache.eviction_algorithm.column_data']
            dynamic_cache_configuration_data = experiment_data[experiment][
                'switch.controller.cache_configuration.column_data']
            switch_str = experiment_data[experiment]['str(switch)']

            for entry in switch_str.split(","):
                key, value = entry.split(":")
                SimulatorIO.create_insert_key(data_out, key.strip(), value.strip())
            for col in in_algo_col_data:
                SimulatorIO.create_insert_key(data_out, col, in_algo_col_data[col])
            for col in evic_algo_col_data:
                SimulatorIO.create_insert_key(data_out, col, evic_algo_col_data[col])
            for col in dynamic_cache_configuration_data:
                SimulatorIO.create_insert_key(data_out, col, dynamic_cache_configuration_data[col])
            SimulatorIO.create_insert_key(data_out, "Main Cache Delay", slow_cache_delay)
            SimulatorIO.create_insert_key(data_out, "Main Cache Size", slow_cache_size)
            SimulatorIO.create_insert_key(data_out, "Secondary Cache Delay", fast_cache_delay)
            SimulatorIO.create_insert_key(data_out, "Secondary Cache Size", fast_cache_size)

        return pd.DataFrame.from_dict(data_out)

    @staticmethod
    def truncate_and_recalculate_result_json(json_path, save_to_dir, start_time, end_time):
        with open(json_path) as f:
            experiment_data = json.load(f)

        new_json_path = save_to_dir + json_path.split('/')[-1]

        new_experiment_data = {}
        for experiment in experiment_data:
            event_logger, time_slice, switch_str, in_algo_col_data, evic_algo_col_data = experiment_data[experiment]
            new_event_loggr = TimeSeriesLogger(time_slice)
            # calculate new event logger
            for event, event_ts in zip(event_logger, time_slice):
                start_idx = int(start_time / time_slice[event_ts])
                end_idx = int(end_time / time_slice[event_ts])
                new_event_loggr.event_logger[int(event)] = event_logger[event][start_idx:end_idx]
            # calculate new switch_str
            new_switch_str = Switch.get_switch_str(new_event_loggr)
            new_experiment_data[experiment] = [new_event_loggr.event_logger,
                                               time_slice,
                                               new_switch_str,
                                               in_algo_col_data,
                                               evic_algo_col_data]

        with open(new_json_path, 'w') as f:
            json.dump(new_experiment_data, f)

    @staticmethod
    def join_all_experiment_csv(input_path):
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

        print(input_path + '/' + 'complete_summary.csv')
        combine_csv.save_new_csv(input_path + '/' + 'complete_summary.csv')

    @staticmethod
    def select_configuration(df, cache_size, controller_delay, experiment_name):
        if experiment_name:
            return df[(df['Cache Size'] == cache_size) &
                      (df['Controller Delay'] == controller_delay) &
                      (df['Experiment Name'] == experiment_name)]
        else:
            return df[(df['Cache Size'] == cache_size) &
                      (df['Controller Delay'] == controller_delay)]

    @staticmethod
    def compare_dynamic_and_static(dynamic_summary_csv, static_summary_csv, output_path):
        dynamic_df = pd.read_csv(dynamic_summary_csv)
        static_df = pd.read_csv(static_summary_csv)
        experiment_name_array = np.unique(dynamic_df[
                                              'Experiment Name']) if 'Experiment Name' in dynamic_df.columns else [None]
        cache_size_array = np.unique(dynamic_df['Cache Size'])
        controller_delay_array = np.unique(dynamic_df['Controller Delay'])
        result_df = pd.DataFrame()
        for experiment_name in experiment_name_array:
            for controller_delay in controller_delay_array:
                for cache_size in cache_size_array:
                    tmp_dynamic_df = SimulatorIO.select_configuration(dynamic_df,
                                                                      cache_size,
                                                                      controller_delay,
                                                                      experiment_name)
                    result_dynamic_df = tmp_dynamic_df[(tmp_dynamic_df['Total Hits Percent'] ==
                                                        tmp_dynamic_df['Total Hits Percent'].max())]
                    tmp_static_df = SimulatorIO.select_configuration(static_df,
                                                                     cache_size,
                                                                     controller_delay,
                                                                     experiment_name)
                    result_static_df = tmp_static_df[(tmp_static_df['Total Hits Percent'] ==
                                                      tmp_static_df['Total Hits Percent'].max())]
                    result_df = pd.concat([result_df, result_dynamic_df, result_static_df])
        result_df.to_csv(output_path)

    @staticmethod
    def compress_complete_summary(static_summary_csv):
        static_df = pd.read_csv(static_summary_csv)
        experiment_name_array = np.unique(static_df[
                                              'Experiment Name']) if 'Experiment Name' in static_df.columns else [None]
        cache_size_array = np.unique(static_df['Cache Size'])
        controller_delay_array = np.unique(static_df['Controller Delay'])
        result_df = pd.DataFrame()
        for experiment_name in experiment_name_array:
            for controller_delay in controller_delay_array:
                for cache_size in cache_size_array:
                    tmp_static_df = SimulatorIO.select_configuration(static_df,
                                                                     cache_size,
                                                                     controller_delay,
                                                                     experiment_name)
                    result_static_df = tmp_static_df[(tmp_static_df['Total Hits Percent'] ==
                                                      tmp_static_df['Total Hits Percent'].max())]
                    result_df = pd.concat([result_df, result_static_df])
        result_df.to_csv('SimulatorTrace/complete_summary_compressed.csv')
