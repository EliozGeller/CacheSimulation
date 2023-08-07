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

#ifndef __SIGMETRICS24_TCX_H
#define __SIGMETRICS24_TCX_H

#include <omnetpp.h>
#include <map>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <vector>
#include <algorithm>
#include <chrono>
#include <fstream>

using namespace omnetpp;
using namespace std;

#define NUM_OF_ToRs 10

namespace sigmetrics24 {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Txc : public cSimpleModule
{
  private:
    double cost_model[3] = {0,0.1,1};
    double alpha;
    int k[NUM_OF_ToRs];
    int k_agg;
    //variables for all algorithms:
    uint64_t t = 1; //time t
    uint64_t r; //the rule arrive at time t
    int j; // The ToR arrive for it packet at time t
    int m = NUM_OF_ToRs;
    std::map<uint64_t, uint64_t> tor[NUM_OF_ToRs];
    std::map<uint64_t, uint64_t> agg;
    int tor_cache_size[NUM_OF_ToRs] = {0};
    int agg_cache_size = 0;
    int number_of_uniqe_flows = 35703;
    long double total_miss_cost = 0;
    long double total_insertion_cost = 0;


    //Read the traffic:
    std::vector<std::vector<uint64_t>> traffic[NUM_OF_ToRs];
    uint32_t index_of_file[NUM_OF_ToRs] = {0};
    uint64_t traffic_size[NUM_OF_ToRs] = {0};

    //Hit Ratio:
    uint64_t total_traffic_Agg = 0;
    uint64_t num_Hit_ToR = 0;
    uint64_t num_Hit_Agg = 0;



  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual void insert_rule_to(string where_to_insert);
    virtual long double miss_cost_at_time_t();
    virtual bool get_packet(uint64_t* r,int* j);
};

}; // namespace

#endif
