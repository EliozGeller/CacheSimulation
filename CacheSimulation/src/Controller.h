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
#include "Definitions.h"
#include "messages_m.h"
#include <map>

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Controller : public cSimpleModule
{
  private:
    uint64_t policy_size;
    int num_of_ToRs;
    simtime_t processing_time_on_data_packet_in_controller;
    unsigned long long int byte_counter;
    string algorithm;
    partition_rule* partition;
    int miss_table_size;
    cHistogram bandwidth_hist;
    std::map<uint64_t, controller_rule> controller_policy;
    uint64_t insertion_rate = 0;

    int diversity_th;
    int count_th;
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual void partition_calculation(Data_for_partition* msg);
    virtual void update_miss_forwarding();
    virtual void set_all_parameters();
    virtual void initialization_start_time_for_flows();
    virtual void set_controller_policy(uint64_t policy_size);
    virtual void send_rule(uint64_t rule,int agg_destination,int tor_destination,string action_con_sw,string action_agg,string action_tor);
    //virtual uint64_t draw_flow_size();
};

}; // namespace

#endif
