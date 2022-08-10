import os
import sys
import concurrent.futures
from multiprocessing import Process

sys.path.append('../')
from TrafficGenerator.ApplicationGenerator import OnlineApplicationGenerator, ApplicationGenerator
from TrafficGenerator.PacketScheduler import PacketScheduler
from TimeSeriesLogger import *
from concurrent.futures import ProcessPoolExecutor


class TGScenario:
    @staticmethod
    def run_experiment(n_flows,
                       flow_distribution_path,
                       flow_distribution_pdf,
                       flowlet_break_count,
                       flow_per_sec,
                       flowlet_per_sec,
                       packet_per_sec,
                       work_dir,
                       deficit_param,
                       time_limit
                       ):
        """
        Used to define a Traffic Generator configuration
        :param deficit_param: Deficit parameter for the scheduling algorithm
        :param n_flows: Number of flows
        :param flow_distribution_path: CDF file (csv) of flow size (check data/)
        :param flow_distribution_pdf: Optional (can be None) to change the flow size distribution manually
        :param flowlet_break_count: define how many flowlets are generated from flow
        :param policy: Policy object (../Policy.py)
        :param flow_per_sec: Time generation function (incremental)
        :param flowlet_per_sec: Time generation function (incremental)
        :param packet_per_sec: Line rate in packet/sec - default: 100k pps
        :param work_dir: Target dir to save the output files
        :return:
        """
        path_save_flow_array = work_dir + 'flow_trace.json'
        path_save_flowlet_array = work_dir + 'flowlet_trace.json'
        path_save_packet_array = work_dir + 'packet_trace.json'

        online_application_generator = OnlineApplicationGenerator(n_flows,
                                                                  flow_distribution_path,
                                                                  flowlet_break_count,
                                                                  10000,
                                                                  lambda: np.random.exponential(1 / flow_per_sec),
                                                                  lambda: np.random.exponential(
                                                                      1 / flowlet_per_sec),
                                                                  time_limit=100,
                                                                  path_save_flow_array=path_save_flow_array,
                                                                  path_save_flowlet_array=path_save_flowlet_array,
                                                                  flow_distribution_pdf=flow_distribution_pdf)
        packet_scheduler = PacketScheduler(online_application_generator, lambda: 1 / packet_per_sec,
                                           path_save_packet_array=path_save_packet_array,
                                           deficit_param=deficit_param,
                                           time_limit=time_limit)
        online_application_generator.generate()
        print("finished generating flows and flowlets")
        packet_scheduler.generate_packets()
        print("done")


def define_task_array():
    """
    Define multiple TGScenario objects and run them in parallel using the python multiprocessing library"
    """
    idx = int(sys.argv[1])
    print("idx: {0}".format(idx))
    task_array = []
    cdf_file_path_array = [
        '../data/websearch.csv',  # Work! don't touch!
        '../data/datamining.csv',  # TODO
        '../data/FB_Hadoop_Inter_Rack_FlowCDF.csv',  # TODO
        '../data/pareto.csv',  # TODO
    ]
    cdf_file_path_array = [cdf_file_path_array[idx]]
    flowlet_break_count = 1  # no flowlets
    packet_per_sec = 100000  # Line Rate
    n_flows_array = [100,100,100]  # How many flow to generate
    flows_per_sec_array = [100,100]  # Inter arrival time between flows
    flowlet_per_sec_array = [1000]  # Inter arrival time between flowlets
    deficit_param_array = [10]  # INF # [10, 100, 1000] # how many to pull from each queue
    time_limit = 600
    for flow_distribution_path in cdf_file_path_array:
        flow_distribution_name = flow_distribution_path.split('/')[-1].split('.')[0]
        for n_flows in n_flows_array:
            for flow_per_sec in flows_per_sec_array:
                for flowlet_per_sec in flowlet_per_sec_array:
                    for deficit_param in deficit_param_array:
                        work_dir = 'Traces/elioz/' + flow_distribution_name + '_n_flows' + str(
                            n_flows) + '_elioz' + str(
                            deficit_param) + '_flow_per_sec' + str(
                            flow_per_sec) + '_flowlet_per_sec' + str(flowlet_per_sec) + '/'
                        if not os.path.isdir(work_dir):
                            os.makedirs(work_dir)
                        task_array.append((n_flows,
                                           flow_distribution_path,
                                           None,
                                           flowlet_break_count,
                                           flow_per_sec,
                                           flowlet_per_sec,
                                           packet_per_sec,
                                           work_dir,
                                           deficit_param,
                                           time_limit
                                           ))
    return task_array


def run_concurrent_tasks():
    task_array = define_task_array()
    print(len(task_array))
    execute(task_array, TGScenario.run_experiment)


def execute(executor_arguments_array, target_func):
    """
    executor_arguments_array - Arguments for target_func
    target_func - function to run concurrently
    """

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


def main():
    run_concurrent_tasks()


if __name__ == "__main__":
    main()
