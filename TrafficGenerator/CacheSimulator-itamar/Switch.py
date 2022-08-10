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
import random

from collections import OrderedDict, deque
from TimeSeriesLogger import *


class Cache:
    def __init__(self,
                 eviction_algorithm,
                 slow_cache_size_init,
                 fast_cache_size_init,
                 enable_garbage_collector=True):
        self.cache_max_capacity = slow_cache_size_init + fast_cache_size_init
        self.cache_size = {'fast_cache': fast_cache_size_init,
                           'slow_cache': slow_cache_size_init}
        self.cache_occupancy = {'fast_cache': 0, 'slow_cache': 0}
        self.insertion_delay = {'fast_cache': 5E-3, 'slow_cache': 15E-3}
        self.eviction_algorithm = eviction_algorithm
        self.cache = OrderedDict()
        self.rules_statistics = {}
        self.time_slice_count = 0
        self.rules_lru_bit = {}
        self.FIFO = deque()
        self.enable_garbage_collector = enable_garbage_collector

    def insert_rule(self, rule, action, cache_type):
        if self.cache_size[cache_type] > 0 and self.cache_occupancy[cache_type] < self.cache_size[cache_type]:
            self.rules_statistics[rule] = 1  # Initiate rule's counter.
            if rule not in self.cache:
                self.cache[rule] = cache_type
                self.cache_occupancy[cache_type] += 1
                self.FIFO.append(rule)
            # self.FIFO.append(rule)
            return True
        else:
            return False

    def evict_rule(self):
        rule = self.FIFO.popleft()
        if self.cache.get(rule):
            cache_type = self.cache[rule]
            self.cache_occupancy[cache_type] -= 1
            del self.cache[rule]
        if self.rules_statistics.get(rule):
            del self.rules_statistics[rule]

    def get(self, rule):
        return self.cache.get(rule)

    def get_cache_size(self):
        return len(self.cache)

    def get_cache_max_size(self):
        return self.cache_max_capacity

    def process_event_queue(self, event_queue, arrival_time, insertion_type):
        while event_queue and arrival_time > event_queue[0][0] + self.insertion_delay[insertion_type]:
            event_time, rule, action = event_queue.pop(0)
            if rule is None:
                self.update_cache_split_size(*action)
            if len(self.cache) >= self.cache_max_capacity > 0:
                self.evict_rule()
            self.insert_rule(rule, action, insertion_type)

    def lookup(self, packet, curr_time_slice):
        dst, arrival_time = packet[1], packet[3]
        if self.get(str(dst)) is None:
            return False  # miss
        else:  # hit
            rule, action = dst, self.cache.get(dst)
            self.rules_statistics[rule] = 1 + self.rules_statistics.get(rule, 0)
            self.rules_lru_bit[rule] = 1
        if self.enable_garbage_collector and \
                self.cache_max_capacity > 0 and len(self.cache) / self.cache_max_capacity > 0.95:
            self.garbage_collector(curr_time_slice)

        return True

    def garbage_collector(self, curr_time_slice):
        time_slice_factor = 1
        if curr_time_slice > self.time_slice_count + time_slice_factor:
            idx = np.random.randint(len(self.cache.keys()))
            self.evict_rule()

    def update_cache_split_size(self, slow_cache_size, fast_cache_size):
        # print("self.change_cache_conf : {0}".format((slow_cache_size, fast_cache_size)))
        self.cache_size['fast_cache'] = fast_cache_size
        self.cache_size['slow_cache'] = slow_cache_size


class Switch:
    def __init__(self, controller,
                 eviction_algorithm,
                 slow_cache_size_init,
                 fast_cache_size_init,
                 time_slice,
                 enable_garbage_collector):
        self.cache = Cache(eviction_algorithm, slow_cache_size_init, fast_cache_size_init, enable_garbage_collector)
        self.logger = TimeSeriesLogger.init_time_series_time_slice(time_slice)
        self.controller = controller
        self.switch_unique_flows = set()
        self.controller_unique_flows = set()

    # Packet format - (src_ip, dst_ip, size, time, flow_id)
    def send_to_switch(self, packet):
        # bandwidth to the switch
        packet = (packet[0], packet[1], int(packet[2]), float(packet[3]), packet[4])
        size, arrival_time = packet[2], packet[3]
        self.logger.log_event(EventType.switch_bw, arrival_time, size)
        self.switch_unique_flows.add(packet[1])

        if self.logger.record_one_event(EventType.switch_unique_flow, arrival_time, len(self.switch_unique_flows)):
            self.switch_unique_flows = set()
        if self.logger.record_one_event(EventType.controller_unique_flow, arrival_time, len(self.controller_unique_flows)):
            self.controller_unique_flows = set()

        if not self.controller.algorithm_update_in_controller:
            self.controller.cache_configuration.update_epoch_burst(packet)

        # update cache from future image of the controller and evict if necessary
        self.cache.process_event_queue(self.controller.event_queue['slow_cache'], arrival_time, 'slow_cache')
        self.cache.process_event_queue(self.controller.event_queue['fast_cache'], arrival_time, 'fast_cache')

        cache_hit = self.cache_lookup(packet, arrival_time)
        if not cache_hit:
            self.controller_unique_flows.add(packet[1])
            self.logger.log_event(EventType.controller_bw, arrival_time, size)
            self.controller.cache_miss_handler(packet)  # controller decides to insert or not
            self.logger.log_event(EventType.cache_miss, arrival_time, 1)
        else:  # hit
            self.logger.log_event(EventType.cache_hit, arrival_time, 1)

        return cache_hit

    def cache_lookup(self, packet, arrival_time):
        curr_time_slice = len(self.logger.event_logger[EventType.switch_bw])
        return self.cache.lookup(packet, curr_time_slice)

    def __str__(self):
        return Switch.get_switch_str(self.logger)

    @staticmethod
    def print_cache_statistics(switch):
        total_accesses = switch.logger.sum_all_events(EventType.cache_hit) + switch.logger.sum_all_events(
            EventType.cache_miss)
        total_hits = switch.logger.sum_all_events(EventType.cache_hit)
        total_misses = switch.logger.sum_all_events(EventType.cache_miss)
        print("Admission Algorithm: " + switch.controller.insertion_algorithm.name + " " +
              "Eviction Algorithm: " + switch.cache.eviction_algorithm.name)
        print("Cache Statistics:")
        print("=================")
        print("Total Accesses: " + str(total_accesses))
        print("Total Hits:     " + str(total_hits) + " (" + str(round(float(total_hits / total_accesses) * 100,
                                                                      2)) + "%)")
        print("Total Misses:   " + str(total_misses) + " (" + str(round(float(total_misses / total_accesses) * 100,
                                                                        2)) + "%)")
        print()

    @staticmethod
    def get_switch_str(logger):
        total_accesses = logger.sum_all_events(EventType.cache_hit) + logger.sum_all_events(
            EventType.cache_miss)
        total_hits = logger.sum_all_events(EventType.cache_hit)
        total_misses = logger.sum_all_events(EventType.cache_miss)
        ret_str = "Total Accesses: " + str(total_accesses) + ","
        ret_str += "Total Hits Count: " + str(total_hits) + ", Total Hits Percent :" + str(
            round(float(total_hits / total_accesses) * 100,
                  2))
        ret_str += ", Total Misses: " + str(total_misses) + ", Total Misses Percent: " + str(
            round(float(total_misses / total_accesses) * 100,
                  2))
        return ret_str
