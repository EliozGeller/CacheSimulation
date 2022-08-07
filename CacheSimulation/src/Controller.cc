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

}

void Controller::handleMessage(cMessage *message)
{
    DataPacket *msg = check_and_cast<DataPacket *>(message);
    ControlPacket *conpacket = new ControlPacket("Insert rule Packet");
    conpacket->setKind(INSERTRULE);
    conpacket->setRule(msg->getDestination());
    send(conpacket, "port$o", 0);
    delete msg;

}

}; // namespace
