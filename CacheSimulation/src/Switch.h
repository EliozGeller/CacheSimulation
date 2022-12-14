//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#ifndef __CACHESIMULATION_TCX_H
#define __CACHESIMULATION_TCX_H

#include <omnetpp.h>
#include "messages_m.h"
#include <map>
#include "Definitions.h"


using namespace omnetpp;

namespace cachesimulation {



/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Switch : public cSimpleModule
{
  private:
    int id;
    uint64_t policy_size;
    std::map<uint64_t, ruleStruct> cache;
    std::map<uint64_t, elephant_struct> elephant_table;
    int elephant_table_size = 0;
    int elephant_table_max_size;
    partition_rule* miss_table;
    int miss_table_size;
    unsigned long int cache_size_t = 0;
    unsigned long int elephant_count; //Counter for sampling packets in RX
    unsigned long long int byte_count = 0;
    unsigned long long int byte_count_per_link[100] = {0};
    unsigned long long int before_hit_byte_count[100] = {0};
    unsigned long long int after_hit_byte_count[100] = {0};
    unsigned long long int hit_packets = 0;
    unsigned long long int miss_packets = 0;
    cOutVector misscount;
    unsigned long long int bandwidth_elephant_threshold;
    simtime_t already_requested_threshold;
    cHistogram cache_occupancy;


    unsigned long long int insertion_count_push = 0;
    unsigned long long int insertion_count_pull = 0;
    cHistogram insertion_count;
    cHistogram bandwidth_data;

    //replace to par:
    int type;
    int elephant_sample_rx;
    long double processing_time_on_data_packet_in_sw;
    long double insertion_delay;
    long double cache_percentage;
    unsigned long long cache_size;
    int eviction_sample_size;
    long double eviction_delay;
    long double flush_elephant_time;
    long double check_for_elephant_time;
    int threshold;
    int num_of_agg;


    //flow count:
    cHistogram flow_count_hist;
    std::map<string, int> flow_count;
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual int cache_search(uint64_t rule);
    virtual int miss_table_search(uint64_t rule);
    virtual uint64_t which_rule_to_evict(int s);
    virtual void fc_send(DataPacket *msg);
    virtual int hash(uint64_t dest);
    virtual int hit_forward(uint64_t dest);
    virtual int internal_forwarding_port (InsertionPacket *msg);
    virtual std::string which_switch_i_am();

};

}; // namespace

#endif
