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
#include <map>
#include "messages_m.h"

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Destination : public cSimpleModule
{
  private:
    cHistogram miss_count;
    cHistogram out_of_order;
    unsigned long long int packet_counter;
    std::map<std::string, long long int> expected_sequence;
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual void out_of_order_statistics(DataPacket* msg);
};

}; // namespace

#endif