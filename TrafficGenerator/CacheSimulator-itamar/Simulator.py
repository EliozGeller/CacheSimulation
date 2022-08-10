import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from Algorithm import *
from Controller import Controller
from Switch import Switch
from copy import deepcopy
from multiprocessing import Process, shared_memory
from SimulatorIO import SimulatorIO
from functools import reduce
import cProfile
import pstats

time_idx = 3
enable_garbage_collector = True
algorithm_update_in_controller = True


class Utils:
    @staticmethod
    def ensure_dir(file_path):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def calculate_and_save_clock_offset_per_join_trace(experiment_names, packet_trace_json_path_array, work_dir):
        packet_trace_array = []
        for packet_trace_json_path in packet_trace_json_path_array:
            with open(packet_trace_json_path) as f:
                packet_trace_array.append(json.load(f))

        trace_times_array = [(packet_trace[0][time_idx], packet_trace[-1][time_idx]) for experiment_name, packet_trace
                             in
                             zip(experiment_names, packet_trace_array)]

        trace_times = {}
        clock_offset_array = [0]
        for experiment_name, time in zip(experiment_names, trace_times_array):
            s_t, e_t = time
            curr_clock_offset = clock_offset_array[-1] + e_t + 100 / 100000
            clock_offset_array.append(curr_clock_offset)
            trace_times[experiment_name] = (s_t + curr_clock_offset, e_t + curr_clock_offset)

        with open(work_dir + 'trace_times.json', 'w') as f:
            json.dump(trace_times, f)
        return clock_offset_array

    @staticmethod
    def construct_switch_array(experiment_data_array):
        global algorithm_update_in_controller
        switch_array = []
        global enable_garbage_collector
        for insertion_algorithm, eviction_algorithm, cache_conf in experiment_data_array:
            time_granularity = 0.01
            switch_array.append(Switch(controller=Controller(insertion_algorithm=deepcopy(insertion_algorithm),
                                                             dynamic_cache_configuration=deepcopy(cache_conf),
                                                             time_granularity=time_granularity,
                                                             algorithm_update_in_controller=algorithm_update_in_controller),
                                       eviction_algorithm=deepcopy(eviction_algorithm),
                                       slow_cache_size_init=cache_conf.slow_cache_size_init,
                                       fast_cache_size_init=cache_conf.fast_cache_size_init,
                                       time_slice=time_granularity,
                                       enable_garbage_collector=enable_garbage_collector
                                       ))
        return switch_array

    @staticmethod
    def execute(executor_arguments_array, target_func):
        process_array = []
        for process_arguments in executor_arguments_array:
            process_array.append(Process(target=target_func, args=process_arguments))

        size_process_array = len(process_array)
        print(len(process_array))
        step_size = os.cpu_count()
        for i in range(0, size_process_array, step_size):
            process_to_create = min(step_size, len(process_array) - i)
            print('START: Process ' + str(i) + '...' + str(i + process_to_create))
            for j in range(process_to_create):
                process_array[i + j].start()
            for j in range(process_to_create):
                process_array[i + j].join()
            print('END: Process ' + str(i) + '...' + str(i + process_to_create))


class Algorithms:
    @staticmethod
    def fixed_threshold():
        threshold_values = [2, 8, 14]

        aging_period = 0.01
        aging_factor = 0.5

        insertion_algorithms = [FixedThreshold(th_val, aging_period, aging_factor) for th_val in threshold_values]
        return insertion_algorithms

    @staticmethod
    def dynamic_threshold():
        aging_period = 0.01
        aging_factor = 0.5
        insertion_algorithms = []
        for epoch in [1, 3, 5]:
            insertion_algorithms.append(DynamicThresholdBW(aging_period,
                                                           aging_factor,
                                                           (lambda x: x + 2, "linear_increase_2"),
                                                           (lambda x: x - 2, "linear_decrease_2"),
                                                           epoch))
            # insertion_algorithms.append(DynamicThresholdUniqueFlow(aging_period,
            #                                                        aging_factor,
            #                                                        (lambda x: x + 2, "linear_increase_2"),
            #                                                        (lambda x: x - 2, "linear_decrease_2"),
            #                                                        epoch))
            insertion_algorithms.append(DTHillClimberBW(aging_period,
                                                        aging_factor,
                                                        (lambda x: x + 2, "linear_increase_2"),
                                                        (lambda x: x - 2, "linear_decrease_2"),
                                                        epoch))
            # insertion_algorithms.append(DTHillClimberUniqueFlows(aging_period,
            #                                                      aging_factor,
            #                                                      (lambda x: x + 2, "linear_increase_2"),
            #                                                      (lambda x: x - 2, "linear_decrease_2"),
            #                                                      epoch))

        return insertion_algorithms

    @staticmethod
    def dynamic_cache_configuration(cache_state_array_array):
        aging_period = 0.01
        aging_factor = 0.5
        epoch = 0.01
        dcc = []
        for cache_state_array in cache_state_array_array:
            dcc = dcc + [UniqueFlowsDCC(epoch=epoch,
                                        cache_state_array=cache_state_array,
                                        aging_period=aging_period,
                                        aging_factor=aging_factor),
                         AVGburstDCC(epoch=epoch,
                                     cache_state_array=cache_state_array,
                                     aging_period=aging_period,
                                     aging_factor=aging_factor),
                         BandwidthDCC(epoch=epoch,
                                      cache_state_array=cache_state_array,
                                      aging_period=aging_period,
                                      aging_factor=aging_factor)
                         # CoefficientVarianceDCC(epoch=epoch,
                         #                        cache_state_array=cache_state_array,
                         #                        aging_period=aging_period,
                         #                        aging_factor=aging_factor)
                         ]

        return dcc

    @staticmethod
    def static_cache_configuration(cache_sizes):
        aging_period = 0.01
        epoch = 0.01

        cache_configuration_array = []
        for scs, fsc in cache_sizes:
            cache_configuration_array.append(StaticCacheConfiguration(
                slow_cache_size_init=scs,
                fast_cache_size_init=fsc,
                aging_period=aging_period,
                epoch=epoch))
        return cache_configuration_array


class ExperimentHandler:
    @staticmethod
    def switch_array(policy_size):
        # experiment_data_array = (insertion_algorithm, eviction_algorithm, cache_conf)
        # Create 3-tuples to pass to construct_switch_array as the base of any single experiment
        # Pair of (Utils.switch_array, ExperimentHandler.run_experiment) define task
        """
        Cache sizes 1% 5% 10%
        [[(1%, 0), (0.5%, 0.5%), (0, 1%)], [(5%, 0), (2.5%, 2.5%), (0, 5%)], [(10%, 0), (5%, 5%), (0, 10%)]]
        """
        rnd = lambda v: int(np.ceil(v))
        cache_state_array = [[(rnd(p * policy_size), 0),
                              (rnd(0.5 * p * policy_size), rnd(0.5 * p * policy_size)),
                              (0, rnd(p * policy_size))] for p in (0.01, 0.05, 0.1)]

        insertion_algorithms = Algorithms.fixed_threshold()
        eviction_algorithm = [RandomEviction()]
        # cache_configuration = Algorithms.dynamic_cache_configuration(cache_state_array) + \
        #                       Algorithms.static_cache_configuration(reduce(lambda z, y: z + y, cache_state_array))

        cache_configuration = Algorithms.static_cache_configuration(reduce(lambda z, y: z + y, cache_state_array))
        experiment_data_array = []
        for insertion_algo in insertion_algorithms:
            for eviction_algo in eviction_algorithm:
                for cache_conf in cache_configuration:
                    experiment_data_array.append((insertion_algo, eviction_algo, cache_conf))
        switch_array = Utils.construct_switch_array(experiment_data_array)
        return switch_array

    @staticmethod
    def run_experiment(switch_array, json_path, packet_json_path):
        with open(packet_json_path) as f:
            packet_list = json.load(f)

        len_job = len(switch_array)
        print("Packets in trace: {0}\n".format(len(packet_list)))
        for switch_idx, switch in enumerate(switch_array):
            print("Running Switch {0}/{1}\n".format(switch_idx, len_job))
            t0 = time.time()
            for packet_idx, packet in enumerate(packet_list):
                if packet_idx % 100000 == 0:
                    print(packet_idx)
                    print("Elapsed time: {0}".format(time.time() - t0))
                    if time.time() - t0 > 5 * 60:
                        return
                switch.send_to_switch(packet)
            print("Experiment time: {0}\n".format(time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))))

        # Last one
        print("Running Switch {0}/{1}\n".format(len(switch_array), len_job))

        for switch in switch_array:
            Switch.print_cache_statistics(switch)

        SimulatorIO.experiment_to_json(switch_array, json_path)

        return json_path

    @staticmethod
    def worker(switch, json_path, shm_name, shape, dtype):
        existing_shm = shared_memory.SharedMemory(name=shm_name)
        packet_list = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
        t0 = time.time()
        for packet_idx, packet in enumerate(packet_list):
            switch.send_to_switch(packet)
        print("Saving: {0} Elapsed time: {1}".format(json_path, time.time() - t0))

        Utils.ensure_dir(json_path)
        SimulatorIO.experiment_to_json([switch], json_path)

    @staticmethod
    def worker_multi_trace(switch, json_path, shm_name, shape, dtype, clock_offset_array):
        existing_shm = shared_memory.SharedMemory(name=shm_name)
        packet_trace_array = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
        t0 = time.time()
        for packet_trace, clock_offset in zip(packet_trace_array, clock_offset_array):
            for packet in packet_trace:
                packet[time_idx] = float(packet[time_idx]) + clock_offset
                switch.send_to_switch(packet)
        print("Saving: {0} Elapsed time: {1}".format(json_path, time.time() - t0))
        Utils.ensure_dir(json_path)
        SimulatorIO.experiment_to_json([switch], json_path)


    @staticmethod
    def run_experiment_multi_trace(switch_array,
                                   json_path,
                                   packet_trace_json_path_array,
                                   clock_offset_array):
        print(json_path.split('/')[-1])
        packet_trace_array = []
        for packet_trace_json_path in packet_trace_json_path_array:
            with open(packet_trace_json_path) as f:
                packet_trace_array.append(json.load(f))

        for switch_idx, switch in enumerate(switch_array):
            print("Running Switch {0}/{1}\n".format(switch_idx, len(switch_array)))
            for packet_trace, clock_offset in zip(packet_trace_array, clock_offset_array):
                for packet in packet_trace:
                    packet[time_idx] += clock_offset
                    switch.send_to_switch(packet)
        print("Running Switch {0}/{1}\n".format(len(switch_array), len(switch_array)))

        for switch in switch_array:
            Switch.print_cache_statistics(switch)
        SimulatorIO.experiment_to_json(switch_array, json_path)

        return json_path


class RunDef:
    @staticmethod
    def run_parallel_single_trace(workdir, packet_json_path, policy_size):
        switch_array = ExperimentHandler.switch_array(policy_size)
        with open(packet_json_path, 'r') as f:
            packet_trace = json.load(f)

        np_packet_trace = np.array(packet_trace)
        shape_npt = np_packet_trace.shape
        dtype_npt = np_packet_trace.dtype
        del packet_trace
        shm = shared_memory.SharedMemory(create=True, size=np_packet_trace.nbytes)
        shm_packet_trace = np.ndarray(shape_npt, dtype=dtype_npt, buffer=shm.buf)
        shm_packet_trace[:] = np_packet_trace[:]  # copy to shared memory
        del np_packet_trace
        args = []
        for switch in switch_array:
            exp_key = SimulatorIO.create_experiment_key(switch)
            exp_json = workdir + exp_key + '.json'
            if os.path.exists(exp_json):
                print("==== {0} ALREADY EXISTS ===".format(exp_json))
                continue
            else:
                print("==== CREATING {0} ===".format(exp_json))
                args.append((switch,
                             exp_json,
                             shm.name,
                             shape_npt,
                             dtype_npt))

        Utils.execute(args, ExperimentHandler.worker)

        del shm_packet_trace
        shm.close()
        shm.unlink()

    @staticmethod
    def run_parallel_joined_trace(work_dir, packet_trace_json_path_array, policy_size):
        switch_array = ExperimentHandler.switch_array(policy_size)
        packet_trace_array = []
        for packet_trace_json_path in packet_trace_json_path_array:
            with open(packet_trace_json_path) as f:
                packet_trace_array.append(json.load(f))

        clock_offset_array = Utils.calculate_and_save_clock_offset_per_join_trace(packet_trace_json_path_array,
                                                                                  packet_trace_json_path_array,
                                                                                  work_dir)

        np_packet_trace_array = np.array(packet_trace_array)
        shape_npt = np_packet_trace_array.shape
        dtype_npt = np_packet_trace_array.dtype
        del packet_trace_array
        shm = shared_memory.SharedMemory(create=True, size=np_packet_trace_array.nbytes)
        shm_packet_trace_array = np.ndarray(shape_npt, dtype=dtype_npt, buffer=shm.buf)
        shm_packet_trace_array[:] = np_packet_trace_array[:]  # copy to shared memory
        del np_packet_trace_array

        args = []
        for switch in switch_array:
            exp_key = SimulatorIO.create_experiment_key(switch)
            exp_json = work_dir + exp_key + '.json'
            if os.path.exists(exp_json):
                print("==== {0} ALREADY EXISTS ===".format(exp_json))
                continue
            else:
                print("==== CREATING {0} ===".format(exp_json))
                args.append((switch,
                             exp_json,
                             shm.name,
                             shape_npt,
                             dtype_npt,
                             clock_offset_array))

        Utils.execute(args, ExperimentHandler.worker_multi_trace)

        del shm_packet_trace_array
        shm.close()
        shm.unlink()



def main():
    """
    TODO
    - Resolve cache sizes (1%, 5%, 10%)
    - Understand
    :return:
    """
    val = int(sys.argv[1])
    # date = "2305_{0}".format(sys.argv[2])
    date = "3005"
    global algorithm_update_in_controller
    # algorithm_update_in_controller = eval(sys.argv[2])

    if val == 0:
        # Caida
        # n_packets = 22 239 918
        work_dir = "SimulatorTrace/" + date + "/caida_trace_srcdst/"
        print(work_dir)
        json_path = work_dir + "caida_json.json"
        packet_json_path = "TGDriverCode/Traces/caida_srcdst/packet_trace.json"
        policy_size = 1000000  # 1191271

        work_dir = "SimulatorTrace/" + date + "/short_trace_tst/"
        policy_size = 10
        # packet_json_path = "TGDriverCode/Traces/short_trace/packet_trace.json"
        # policy_size = 1000  # 1191271
        RunDef.run_parallel_single_trace(work_dir, packet_json_path, policy_size)

    if val == 1:
        # Facebook
        work_dir = "SimulatorTrace/" + date + "/fb_clusterA_full_10M/"
        json_path = work_dir + "fb_clusterA_full_10M.json"

        packet_json_path = "TGDriverCode/Traces/fb_clusterA_full_10M/packet_trace.json"
        policy_size = 3000000  # 3134239
        RunDef.run_parallel_single_trace(work_dir, packet_json_path, policy_size)

    if val == 2:
        # run_joined_trace(work_dir, packet_trace_json_path_array) # FB
        work_dir = "SimulatorTrace/" + date + "/FB/"
        packet_trace_json_path_array = [
            "uniform_dst/FB_Hadoop_Inter_Rack_FlowCDF_n_flows50000_deficit_param10_flow_per_sec80_flowlet_per_sec1",
            "uniform_dst/FB_Hadoop_Inter_Rack_FlowCDF_n_flows50000_deficit_param100_flow_per_sec80_flowlet_per_sec1",
            # "uniform_dst/FB_Hadoop_Inter_Rack_FlowCDF_n_flows50000_deficit_param1000_flow_per_sec80_flowlet_per_sec1"
        ]
        policy_size = 6000
        RunDef.run_joined_trace(work_dir,
                                ["TGDriverCode/Traces/" + packet_trace + "/packet_trace.json" for packet_trace in
                                 packet_trace_json_path_array], policy_size)

    if val == 3:
        # run_joined_trace(work_dir, packet_trace_json_path_array) # websearch
        work_dir = "SimulatorTrace/" + date + "/websearch/"
        packet_trace_json_path_array = [
            "uniform_dst/websearch_n_flows50000_deficit_param10_flow_per_sec80_flowlet_per_sec1",
            "uniform_dst/websearch_n_flows50000_deficit_param100_flow_per_sec80_flowlet_per_sec1",
            # "uniform_dst/websearch_n_flows50000_deficit_param1000_flow_per_sec80_flowlet_per_sec1"
        ]
        policy_size = 6000
        RunDef.run_joined_trace(work_dir,
                                ["TGDriverCode/Traces/" + packet_trace + "/packet_trace.json" for packet_trace in
                                 packet_trace_json_path_array], policy_size)


if __name__ == "__main__":
    main()
