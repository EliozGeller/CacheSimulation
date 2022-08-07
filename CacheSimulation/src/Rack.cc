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

#include "Rack.h"
#include "Definitions.h"
#include "messages_m.h"

namespace cachesimulation {

Define_Module(Rack);

void Rack::initialize()
{
    cPacket *message = new cPacket("Generate packet message");
    message->setKind(GENERATEPACKET);
    simtime_t arrival_time = exponential(RACKRATE);
    scheduleAt(simTime() + arrival_time,message);
}

void Rack::handleMessage(cMessage *message)
{
   switch(message->getKind()){
        case GENERATEPACKET:
          DataPacket *msg = new DataPacket("Data Packet");
          msg->setKind(DATAPACKET);
          uint64_t destination = (uint64_t)uniform(0,POLICYSIZE);
          EV << "destination = "<< destination<< endl;
          send(msg, "port$o", 0);
          simtime_t arrival_time = exponential(RACKRATE);
          scheduleAt(simTime() + arrival_time,message);
          break;
    }
}

}; // namespace
