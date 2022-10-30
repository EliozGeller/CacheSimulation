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
#include "Definitions.h"

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Hub : public cSimpleModule
{
private:
    cQueue msg_queue;
  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual void my_send(cMessage *msg);
};

}; // namespace

#endif




namespace cachesimulation {

Define_Module(Hub);

void Hub::initialize()
{

}

void Hub::handleMessage(cMessage *msg)
{
    //send(message, "port$o", 0);


    if(msg->getKind() != HUB_QUEUE_MSG){// packet from host
        my_send(msg);
    }
    else {//schedule packet from queue
        if(msg_queue.isEmpty())return;
        cMessage *pkt = (cMessage *)msg_queue.pop();
        my_send(pkt);
        if(msg)delete msg;
        return;
    }
}

void Hub::my_send(cMessage *msg){

    cChannel *txChannel = gate("port$o",0)->getTransmissionChannel();
    simtime_t txFinishTime = txChannel->getTransmissionFinishTime();
    if (txFinishTime <= simTime())
    {
    // channel free; send out packet immediately
       send(msg, "port$o",0);
    }
    else
    {
    // store packet and schedule timer; when the timer expires,
    // the packet should be removed from the queue and sent out
       msg_queue.insert(msg);
       cMessage *q_msg = new cMessage("Queue_msg");
       q_msg->setKind(HUB_QUEUE_MSG);//Kind of Queue message
       scheduleAt(txFinishTime, q_msg);
    }
}
}; // namespace
