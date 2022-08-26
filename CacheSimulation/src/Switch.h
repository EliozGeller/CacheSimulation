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
    std::map<uint64_t, ruleStruct> cache;
    std::map<uint64_t, elephant_struct> elephant_table;
    partition_rule* miss_table;
    int miss_table_size;
    unsigned long int elephant_count; //Counter for sampling packets in RX
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

};

}; // namespace

#endif
