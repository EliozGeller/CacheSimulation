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

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Controller : public cSimpleModule
{
  private:
    unsigned long long int packet_counter;
    partition_rule* partition;
    int miss_table_size;
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual void partition_calculation(Data_for_partition* msg);
    virtual void update_miss_forwarding();
    virtual void set_all_parameters();
    virtual void initialization_start_time_for_flows();
};

}; // namespace

#endif
