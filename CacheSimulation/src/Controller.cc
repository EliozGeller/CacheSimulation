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


namespace cachesimulation {

Define_Module(Controller);

void Controller::initialize()
{
    packet_counter = 0;

    // Define the initial partition
    miss_table_size = getParentModule()->par("NumOfAggregation");
    partition = new partition_rule[miss_table_size];

    uint64_t last = 0;
    uint64_t diff = (uint64_t)(POLICYSIZE/(int)(getParentModule()->par("NumOfAggregation")));
    for(int i = 0;i < miss_table_size;i++){
        partition[i].low = last;
        partition[i].high = last + diff;
        partition[i].port = i + 1;
        last = last + diff + 1;
    }
    // End Define the initial partition


    //Start scheduling partition messages
    //Data_for_partition* pkt = new Data_for_partition("Data for partition msg");
    //pkt->setKind(DATA_FOR_PARTITION);
    //sendDelayed(pkt, PARTITION_RATE, "port$o", 0);




}

void Controller::handleMessage(cMessage *message)
{
    DataPacket *msg;
    InsertionPacket *conpacket;
    Data_for_partition *pkt;
    switch(message->getKind()){
    case DATAPACKET:
        packet_counter++;
        msg = check_and_cast<DataPacket *>(message);
        conpacket = new InsertionPacket("Insert rule Packet");
        conpacket->setKind(INSERTRULE_PUSH);
        conpacket->setRule(msg->getDestination());
        send(conpacket, "port$o", 0);
        msg->setExternal_destination(1);
        msg->setKind(HITPACKET);
        send(msg, "port$o", 0);
        break;
    case DATA_FOR_PARTITION:
        pkt = check_and_cast<Data_for_partition *>(message);
        partition_calculation(pkt);
        update_miss_forwarding();
        sendDelayed(pkt, PARTITION_RATE, "port$o", 0);
        break;

    }

}

void Controller::partition_calculation(Data_for_partition* msg){

}

void Controller::update_miss_forwarding(){

}

void Controller::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Total arrived packets in the Controller:   " << packet_counter << endl;
    EV << "Time in the Controller:   " << simTime() << endl;
    EV << "Average throughput in the Controller:   " << (float)(packet_counter / simTime()) << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    delete[] partition;
}


}; // namespace
