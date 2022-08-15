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

#include "Controller.h"
#include "Definitions.h"
#include "messages_m.h"


namespace cachesimulation {

Define_Module(Controller);

void Controller::initialize()
{
    packet_counter = 0;
}

void Controller::handleMessage(cMessage *message)
{
    packet_counter++;
    DataPacket *msg = check_and_cast<DataPacket *>(message);
    ControlPacket *conpacket = new ControlPacket("Insert rule Packet");
    conpacket->setKind(INSERTRULE);
    conpacket->setRule(msg->getDestination());
    send(conpacket, "port$o", 0);
    msg->setExternal_destination(1);
    msg->setKind(HITPACKET);
    send(msg, "port$o", 0);

}

void Controller::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Total arrived packets in the Controller:   " << packet_counter << endl;
    EV << "Time in the Controller:   " << simTime() << endl;
    EV << "Average throughput in the Controller:   " << (float)(packet_counter / simTime()) << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
}


}; // namespace
