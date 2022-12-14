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

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Host : public cSimpleModule
{
private:
   int id;
   uint64_t destination;
   long long int flow_size; //in bytes
   long double rate;
   long long int flowlet_size;
   int number_of_flowlet;
   int flowlet_count;
   uint64_t sequence;
   simtime_t inter_arrival_time_between_packets;
   simtime_t inter_arrival_time_between_flowlets;
   simtime_t inter_arrival_time_between_flows;
   cMessage *genpack = nullptr;
   bool first;
  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual void finish();
    virtual void start_flow(simtime_t arrival_time);
    virtual uint64_t draw_flow_size();
    virtual long double draw_rate(int mean);
};

}; // namespace

#endif
