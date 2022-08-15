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




#include "Destination.h"
#include "Definitions.h"
#include "messages_m.h"


namespace cachesimulation {

Define_Module(Destination);

void Destination::initialize()
{
    miss_count.setName("miss count");
}

void Destination::handleMessage(cMessage *message)
{
    EV << "Destination!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    DataPacket *msg = check_and_cast<DataPacket *>(message);
    miss_count.collect(msg->getMiss_hop());
    delete msg;

}

void Destination::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Miss count, mean:   " << miss_count.getMean() << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    miss_count.recordAs("miss count");
}

}; // namespace
