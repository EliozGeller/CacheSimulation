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


class Controller(object):
    def __init__(self,
                 insertion_algorithm=None,
                 dynamic_cache_configuration=None,
                 time_granularity=0.1,
                 algorithm_update_in_controller=True):
        self.insertion_algorithm = insertion_algorithm
        self.insertion_algorithm.set_time_granularity(time_granularity)
        self.cache_configuration = dynamic_cache_configuration
        self.cache_configuration.set_time_granularity(time_granularity)
        self.last_sample = -1
        self.event_queue = {"slow_cache": [], "fast_cache": []}
        self.algorithm_update_in_controller = algorithm_update_in_controller

    def cache_miss_handler(self, packet):
        dst_idx = 1
        time_idx = 3
        rule, action = packet[dst_idx], 0  # exact match
        self.last_sample = float(packet[time_idx])

        if self.algorithm_update_in_controller:
            self.cache_configuration.update_epoch_burst(packet)

        if self.cache_configuration.apply(packet):
            new_cache_configuration = self.cache_configuration.cache_state[
                self.cache_configuration.cache_state_idx]
            # print("new_cache_configuration: {0}".format(new_cache_configuration))
            self.event_queue["fast_cache"].append((packet[time_idx], None, new_cache_configuration))

        if self.insertion_algorithm and self.insertion_algorithm.insertion(rule, action, float(packet[time_idx])):  # sample
            self.event_queue["slow_cache"].append((packet[time_idx], rule, action))

        self.event_queue["fast_cache"].append((packet[time_idx], rule, action))
