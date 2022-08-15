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



namespace cachesimulation {

Define_Module(Destination);

void Destination::initialize()
{
    miss_count.setName("miss count");
    out_of_order.setName("out of order");
    packet_counter = 0;
}

void Destination::handleMessage(cMessage *message)
{
    packet_counter++;
    DataPacket *msg = check_and_cast<DataPacket *>(message);
    EV <<" id = " <<msg->getId() << endl;

    //statistics for miss count
    miss_count.collect(msg->getMiss_hop());

    //statistics for out of order
    out_of_order_statistics(msg);

    delete msg;

}

void Destination::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Miss count in the Destination, mean:   " << miss_count.getMean() << endl;
    EV << "Total arrived packets in the Destination:   " << packet_counter << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    miss_count.recordAs("miss count");
    out_of_order.recordAs("out of order");
}

void Destination::out_of_order_statistics(DataPacket* msg)
{
    long long int diff = get_sequence(msg->getId()) - expected_sequence[get_flow(msg->getId())];
    out_of_order.collect(diff);
    expected_sequence[get_flow(msg->getId())] = get_sequence(msg->getId());
}


}; // namespace
