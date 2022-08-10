#!/usr/bin/env python

"""
Cache Simulator Project
Copyright(c) 2020-2021
This program is free software; you can redistribute it and/or modify it
under the terms and conditions of the GNU General Public License,
version 2, as published by the Free Software Foundation.
This program is distributed in the hope it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.
You should have received a copy of the GNU General Public License along
with this program.  If not, see <http://www.gnu.org/licenses/>.
The full GNU General Public License is included in this distribution in
the file called "COPYING".
Contact Information:
Erez Alfasi <erez8272@gmail.com>
Itamar Gozlan <itamar.goz@gmail.com>
"""
import abc
import random
from abc import ABC

from Switch import Cache
from TimeSeriesLogger import *


class InsertionAlgorithm(metaclass=abc.ABCMeta):
    """
    Abstract class for the insertion algorithm used by the controller
    """

    @abc.abstractmethod
    def __init__(self):
        self.name = "ABC InsertionAlgorithm"
        self.column_data = {
            "In.": None,
            "Threshold": None,
            "Epoch": None,
            "Trend Factor": None,
            "Increase Method": None,
            "Decrease Method": None,
            "In. Aging Period": None,
            "In. Aging Factor": None
        }

    def set_time_granularity(self, time):
        self.logger = TimeSeriesLogger.init_time_series_time_slice(time)

    @abc.abstractmethod
    def insertion(self, rule, action, packet_time):
        pass

    @abc.abstractmethod
    def initialize_column_data(self):
        pass


class FixedThreshold(InsertionAlgorithm):
    """
    FixedThreshold algorithm that determine whether to insert or dismiss a rule to the big_cache only after appear above
    some threshold. The appearances count is multiplied with decay factor every fixed time interval
    """

    def __init__(self, threshold, aging_period, aging_factor):
        InsertionAlgorithm.__init__(self)
        self.aging_period = aging_period
        self.threshold = threshold
        self.aging_factor = aging_factor
        self.clock = 0
        self.name = "FixedThreshold_" + str(threshold) + "_" + str(aging_period) + "_" + str(aging_factor)
        self.initialize_column_data()
        self.counter = 0
        self.pending = {}

    def insertion(self, rule, action, packet_time):
        if packet_time > self.clock + self.aging_period:
            self.clock = packet_time
            self.counter += 1

        value, last_update = self.pending.get(rule, (0, self.counter))
        value = 1 + value * (self.aging_factor ** (self.counter - last_update))  # how many time periods have past
        if value > self.threshold:
            self.pending[rule] = (value, self.counter)
            return True
        else:
            self.pending[rule] = (value, self.counter)
            return False

    def initialize_column_data(self):
        self.column_data.update({
            "In.": "FixedThreshold",
            "Threshold": str(self.threshold),
            "In. Aging Period": str(self.aging_period),
            "In. Aging Factor": str(self.aging_factor)
        })


class DynamicThreshold(InsertionAlgorithm, metaclass=abc.ABCMeta):
    """
    DynamicThreshold algorithm that determine whether to insert or dismiss a rule to the big_cache only after appear above
    some threshold. The appearances count is multiplied with decay factor every fixed time interval. The threshold is
    used to adjust the switch big_cache insertion, When the bw is high we should decrease the threshold and allow more rules
    insertion, when the bw is low, we have a "good" snapshot of the big_cache and we want to keep it and we should increase
    the threshold.
    """

    def __init__(self,
                 aging_period,
                 aging_factor,
                 threshold_increase_tuple,
                 threshold_decrease_tuple,
                 epoch):
        InsertionAlgorithm.__init__(self)
        # decay
        self.aging_period = aging_period
        self.aging_factor = aging_factor
        self.clock = 0
        self.pending = {}

        # dynamic threshold
        self.min_threshold_val = 2
        self.threshold = 2
        self.counter = 0
        self.threshold_increase = threshold_increase_tuple[0]
        self.threshold_decrease = threshold_decrease_tuple[0]
        self.log_unique_rules = False
        self.unique_rules = set()
        self.sensitivity = 0.02

        # Epoch
        self.elapsed_time_last_epoch = 0
        self.epoch = epoch
        self.epoch_counter = 0
        self.prev_epoch_value = 0

        # IO
        self.name = "DynamicThreshold_" + str(epoch) + "_" + str(aging_period) + "_" + str(
            aging_factor) + "_" + threshold_increase_tuple[1] + "_" + \
                    threshold_decrease_tuple[1]
        self.initialize_column_data()

    def initialize_column_data(self):
        threshold_increase = "_".join(self.name.split("_")[-4:-2])
        threshold_decrease = "_".join(self.name.split("_")[-2:])
        self.column_data.update({
            "In.": "DynamicThreshold_" + str(self.threshold) + "_" + str(self.aging_period) + "_" + str(
                self.aging_factor),
            "Epoch": str(self.epoch),
            "Increase Method": threshold_increase,
            "Decrease Method": threshold_decrease,
            "In. Aging Period": str(self.aging_period),
            "In. Aging Factor": str(self.aging_factor)
        })

    def insertion(self, rule, action, packet_time):
        self.logger.log_event(EventType.controller_bw, packet_time, 1)  # time is without delay!
        self.logger.record_one_event(EventType.threshold, packet_time, self.threshold)

        if self.log_unique_rules:
            self.logger.record_one_event(EventType.unique_flow, packet_time, len(self.unique_rules))
            self.unique_rules.add(rule)

        if packet_time > self.clock + self.aging_period:  # self.aging_period has passed
            self.elapsed_time_last_epoch += packet_time - self.clock
            self.clock = packet_time
            self.counter += 1

        if self.elapsed_time_last_epoch > self.epoch:
            self.update_dynamic_threshold()
            self.elapsed_time_last_epoch = 0
            self.epoch_counter += 1
            if self.log_unique_rules:
                self.unique_rules = set()

        value = self.get_value_and_do_decay(rule)
        if value > self.threshold:
            self.pending[rule] = (value, self.counter)
            return True
        else:
            self.pending[rule] = (value, self.counter)
            return False

    def get_value_and_do_decay(self, rule):
        value, last_update = self.pending.get(rule, (0, self.counter))
        value = 1 + value * (self.aging_factor ** (self.counter - last_update))  # how many time periods have past
        return value

    @abc.abstractmethod
    def update_dynamic_threshold(self):
        pass


class DynamicThresholdBW(DynamicThreshold):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = '_'.join(["DynamicThresholdBW"] + self.name.split('_')[1:])

        self.column_data.update({
            "In.": "DynamicThresholdBW" + str(self.aging_period) + "_" + str(
                self.aging_factor)})

    def update_dynamic_threshold(self):
        time_slice = self.logger.time_slice['controller_bw']
        start_idx = int(self.epoch_counter * self.epoch / time_slice)

        epoch_value = np.average(self.logger.event_logger['controller_bw'][start_idx:])
        if (1 + self.sensitivity) * self.prev_epoch_value < epoch_value:  # BW increase in over P -> threshold decrease
            self.threshold = self.threshold_decrease(self.threshold)

        if (1 - self.sensitivity) * self.prev_epoch_value > epoch_value:  # BW decrease in over P - > threshold increase
            self.threshold = self.threshold_increase(self.threshold)

        self.prev_epoch_value = epoch_value
        self.threshold = max(self.min_threshold_val, self.threshold)


class DynamicThresholdUniqueFlow(DynamicThreshold):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = '_'.join(["DynamicThresholdUniqueFlow"] + self.name.split('_')[1:])
        self.column_data.update({
            "In.": "DynamicThresholdUniqueFlow" + str(self.aging_period) + "_" + str(
                self.aging_factor)})
        self.log_unique_rules = True

    def update_dynamic_threshold(self):
        epoch_value = len(self.unique_rules)

        if (1 + self.sensitivity) * self.prev_epoch_value < epoch_value:  # Unique Rules increase -> Increase Threshold
            self.threshold = self.threshold_increase(self.threshold)

        if (1 - self.sensitivity) * self.prev_epoch_value > epoch_value:  # Unique Rules decrease - > Decrease Threshold
            self.threshold = self.threshold_decrease(self.threshold)

        self.prev_epoch_value = epoch_value
        self.threshold = max(self.min_threshold_val, self.threshold)


class DTHillClimberBW(DynamicThreshold):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = '_'.join(["DTHillClimberBW"] + self.name.split('_')[1:])
        self.op = [self.threshold_increase,
                   self.threshold_decrease]
        self.op_state = 0
        self.column_data.update({
            "In.": "DTHillClimberBW_" + str(self.aging_period) + "_" + str(
                self.aging_factor)})

    def update_dynamic_threshold(self):
        time_slice = self.logger.time_slice['controller_bw']
        start_idx = int(self.epoch_counter * self.epoch / time_slice)
        epoch_value = np.average(self.logger.event_logger['controller_bw'][start_idx:])
        if (1 + self.sensitivity) * self.prev_epoch_value < epoch_value:  # BW increase -> change state
            self.op_state = (1 + self.op_state) % 2
            self.threshold = self.op[self.op_state](self.threshold)

        if (
                1 - self.sensitivity) * self.prev_epoch_value > epoch_value:  # BW decrease - > apply state again. keep hypothesis
            self.threshold = self.op[self.op_state](self.threshold)

        self.prev_epoch_value = epoch_value
        self.threshold = max(self.min_threshold_val, self.threshold)


class DTHillClimberUniqueFlows(DynamicThreshold):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = '_'.join(["DTHillClimberUniqueFlows"] + self.name.split('_')[1:])
        self.op = [self.threshold_increase,
                   self.threshold_decrease]
        self.op_state = 0
        self.column_data.update({
            "In.": "DTHillClimberUniqueFlows_" + str(self.aging_period) + "_" + str(
                self.aging_factor)})
        self.log_unique_rules = True

    def update_dynamic_threshold(self):
        epoch_value = len(self.unique_rules)

        if (
                1 + self.sensitivity) * self.prev_epoch_value < epoch_value:  # Unique Rules increase -> apply state again. keep hypothesis
            self.threshold = self.op[self.op_state](self.threshold)

        elif (
                1 - self.sensitivity) * self.prev_epoch_value > epoch_value:  # Unique Rules  decrease - > change hypothesis
            self.op_state = (1 + self.op_state) % 2
            self.threshold = self.op[self.op_state](self.threshold)

        self.prev_epoch_value = epoch_value
        self.threshold = max(self.min_threshold_val, self.threshold)


#######################################################################################################################

class EvictionAlgorithm(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self):
        self.name = "ABC EvictionAlgorithm"
        self.column_data = {"Evic.": None,
                            "Param": None}
        random.seed(0)  # deterministic eviction

    @abc.abstractmethod
    def eviction(self, cache):
        pass

    @abc.abstractmethod
    def initialize_column_data(self):
        pass


class RandomEviction(EvictionAlgorithm):
    def __init__(self):
        EvictionAlgorithm.__init__(self)
        self.name = "Random"
        self.initialize_column_data()

    def eviction(self, cache):
        if cache.get_cache_size() >= cache.get_cache_max_size():
            i = np.random.randint(0, len(cache.cache.keys()))
            cache.evict_rule(list(cache.cache.keys())[i])
            # cache.evict_rule(random.choices(list(cache.cache.keys()), k=1)[0])

    def initialize_column_data(self):
        self.column_data.update({"Evic.": "Random"})


class LFU:
    def __init__(self):
        EvictionAlgorithm.__init__(self)
        self.name = "LFU"
        self.initialize_column_data()

    def eviction(self, cache: Cache):
        if cache.get_cache_size() >= cache.get_cache_max_size():
            cache.evict_rule(min(cache.rules_statistics.items(), key=lambda v: v[1])[0])

    def initialize_column_data(self):
        self.column_data.update({"Evic.": "LFU"})


class LRU:
    def __init__(self):
        EvictionAlgorithm.__init__(self)
        self.name = "LRU"
        self.initialize_column_data()

    def eviction(self, cache: Cache):
        if cache.get_cache_size() >= cache.get_cache_max_size():
            lru_list = list(set(cache.rules_statistics.keys()) - set(cache.rules_lru_bit.keys()))
            if len(lru_list) < 1:
                cache.evict_rule(random.choices(list(cache.rules_statistics.keys()), k=1)[0])
            cache.evict_rule(random.choices(lru_list, k=min(len(lru_list), 1))[0])

    def initialize_column_data(self):
        self.column_data.update({"Evic.": "LRU"})


class FIFO:
    def __init__(self):
        EvictionAlgorithm.__init__(self)
        self.name = "FIFO"
        self.initialize_column_data()

    def eviction(self, cache: Cache):
        if cache.get_cache_size() >= cache.get_cache_max_size():
            victim = cache.FIFO.pop(0)
            cache.evict_rule(victim)

    def initialize_column_data(self):
        self.column_data.update({"Evic.": "FIFO"})


######################################################################################


class CacheConfiguration(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        self.name = "ABC CacheConfiguration"
        self.column_data = {
            "Cache Conf": None,
            "Cache Conf Epoch": None,
        }
        self.slow_cache_size_init = kwargs.get("slow_cache_size_init")
        self.fast_cache_size_init = kwargs.get("fast_cache_size_init")

        self.clock = 0
        self.aging_period = kwargs.get("aging_period")

        # Epoch
        self.elapsed_time_last_epoch = 0
        self.epoch = kwargs.get("epoch")
        self.epoch_counter = 0
        self.prev_epoch_value = 0
        self.counter = 0

        self.logger = TimeSeriesLogger.init_time_series_time_slice(kwargs.get("epoch"))

        # Burst
        self.last_dst = None
        self.curr_burst = 0
        self.epoch_burst = {}
        self.packet_count = 0

    def update_epoch_burst(self, packet):
        self.packet_count += 1
        dst_idx = 1
        self.epoch_burst[packet[dst_idx]] = 1 + self.epoch_burst.get(packet[dst_idx], 0)

    def apply(self, packet):
        time_idx = 3
        size_idx = 2
        packet_size, packet_time = int(packet[size_idx]), float(packet[time_idx])
        if packet_time > self.clock + self.aging_period:  # self.aging_period has passed
            self.elapsed_time_last_epoch += packet_time - self.clock
            self.clock = packet_time
            self.counter += 1

        if self.elapsed_time_last_epoch > self.epoch:
            self.elapsed_time_last_epoch = 0
            self.epoch_counter += 1
            # self.logger.record_one_event(EventType.unique_flow, packet_time, len(self.epoch_burst))
            # self.logger.log_event(EventType.controller_bw, packet_time, packet_size)
            return self.update_cache_state()

        return False

    def set_time_granularity(self, time):
        self.logger = TimeSeriesLogger.init_time_series_time_slice(time)

    @abc.abstractmethod
    def update_cache_state(self):
        pass


class StaticCacheConfiguration(CacheConfiguration, metaclass=abc.ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_data.update({
            "Cache Conf": "StaticCacheConfiguration",
        })
        self.name = "StaticCacheConfiguration"

    def update_cache_state(self):
        return False


class DynamicCacheConfiguration(CacheConfiguration, metaclass=abc.ABCMeta):
    """
    Algorithm that change dynamically the allocated size for the fast insertion and slow insertion
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cache_state_array = kwargs.get("cache_state_array")
        self.slow_cache_size_init = cache_state_array[1][0]
        self.fast_cache_size_init = cache_state_array[1][1]

        self.op_state = 1
        self.cache_state = cache_state_array  # [(0, 30), (15, 15), (30, 0)]
        self.cache_state_idx = 1  # start in even split
        self.sensitivity = 100

        self.initialize_column_data()

    def initialize_column_data(self):
        self.column_data.update({
            "Cache Conf": "DynamicCacheConfiguration",
            "Cache Conf Epoch": self.epoch,
        })

    def update_cache_state(self):
        epoch_value = self.calculate_and_reset_epoch_value()
        alpha = 0.01
        next_epoch_value = (1 - alpha) * self.prev_epoch_value + alpha * epoch_value
        ret_val = False
        if (1 + self.sensitivity) * self.prev_epoch_value < next_epoch_value:  # UF size increase -> fast cache inc
            self.cache_state_idx += 1
            self.cache_state_idx = min(max(0, self.cache_state_idx), len(self.cache_state) - 1)
            ret_val = True

        # UF size decrease -> slow cache inc
        if (1 - self.sensitivity) * self.prev_epoch_value > next_epoch_value:
            # print("Avg burst size decrease - > fast cache inc")
            self.cache_state_idx -= 1
            self.cache_state_idx = min(max(0, self.cache_state_idx), len(self.cache_state) - 1)
            ret_val = True

        self.prev_epoch_value = next_epoch_value

        return ret_val

    @abc.abstractmethod
    def calculate_and_reset_epoch_value(self):
        pass


class UniqueFlowsDCC(DynamicCacheConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_data.update({
            "Cache Conf": "UniqueFlowsDCC",
        })
        self.name = "UniqueFlowsDCC"

    def calculate_and_reset_epoch_value(self):
        epoch_value = len(self.epoch_burst.keys())
        self.epoch_burst = {}
        return epoch_value


class NormalUniqueFlowsDCC(DynamicCacheConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_data.update({
            "Cache Conf": "NormalUniqueFlowsDCC",
        })
        self.name = "NormalUniqueFlowsDCC"

    def calculate_and_reset_epoch_value(self):
        epoch_value = len(self.epoch_burst.keys()) / 100
        self.epoch_burst = {}
        return epoch_value


class AVGburstDCC(DynamicCacheConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_data.update({
            "Cache Conf": "AVGburstDCC",
        })
        self.name = "AVGburstDCC"

    def calculate_and_reset_epoch_value(self):
        epoch_value = sum(self.epoch_burst.values()) / len(self.epoch_burst.keys())
        self.epoch_burst = {}
        return epoch_value


class BandwidthDCC(DynamicCacheConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_data.update({
            "Cache Conf": "BandwidthDCC",
        })
        self.name = "BandwidthDCC"

    def calculate_and_reset_epoch_value(self):
        epoch_value = sum(self.epoch_burst.values())
        self.epoch_burst = {}
        return epoch_value


class CoefficientVarianceDCC(DynamicCacheConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_data.update({
            "Cache Conf": "CoefficientVarianceDCC",
        })
        self.name = "CoefficientVarianceDCC"

    def calculate_and_reset_epoch_value(self):
        epoch_burst_list = list(self.epoch_burst.values())
        epoch_value = np.std(epoch_burst_list) / np.mean(epoch_burst_list)
        self.epoch_burst = {}
        return epoch_value

# class TBD:
#     def update_cache_state_HC(self):
#         pass
#         epoch_value = np.average(self.epoch_burst)
#         # print("epoch_value: {0}".format(epoch_value))
#         self.epoch_burst = []
#         ret_val = False
#         if (1 + self.sensitivity) * self.prev_epoch_value < epoch_value:  # Avg burst size increase -> change state
#             self.op_state = (-1) * self.op_state  # cache configuration change
#             self.cache_state_idx = min(max(0, self.cache_state_idx + self.op_state), len(self.cache_state) - 1)
#             ret_val = True
#
#         # Avg burst size decrease - > apply state again. keep hypothesis
#         if (1 - self.sensitivity) * self.prev_epoch_value > epoch_value:
#             self.cache_state_idx = min(max(0, self.cache_state_idx + self.op_state), len(self.cache_state) - 1)
#             ret_val = True
#
#         self.prev_epoch_value = epoch_value
#         return ret_val
