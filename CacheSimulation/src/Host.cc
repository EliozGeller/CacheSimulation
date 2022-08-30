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

#include "Host.h"

#include "Definitions.h"



#include <fstream>
#include <iostream>
#include <string>
#include <stdlib.h>     /* atoi */





namespace cachesimulation {

Define_Module(Host);

void Host::initialize()
{
    sequence = 0;
    id =  getParentModule()->getIndex() * (int)getParentModule()->par("number_of_hosts") + getIndex();
    EV << "id in rack "<<  getParentModule()->getIndex() << " in Host "<< getIndex() << " is " << id << endl;
    flow_size = draw_destination(); //change
    destination = (uint64_t)uniform(0,POLICYSIZE); //change


    if(flow_size > 100*1000000 /*100 Mbyte*/){
        number_of_flowlet = 10;
    }
    else {
        number_of_flowlet = 1;
    }
    flowlet_size = flow_size/number_of_flowlet;
    flowlet_count = 0;

    //generate first packet:
    DataPacket *message = new DataPacket("Generate packet message");
    message->setKind(GENERATEPACKET);
    scheduleAt(simTime() + exponential(INTER_ARRIVAL_TIME_BETWEEN_PACKETS),message);
}

void Host::handleMessage(cMessage *message)
{
   simtime_t arrival_time;
   switch(message->getKind()){
        case GENERATEPACKET:
          {
          DataPacket *genpack = check_and_cast<DataPacket *>(message);
          DataPacket *msg = new DataPacket("Data Packet");
          msg->setKind(DATAPACKET);
          msg->setDestination(destination);
          std::string str_id = create_id(id,flowlet_count,sequence);
          EV << "id = "<< str_id << endl;
          msg->setId(str_id.c_str());
          int size = 1500;
          msg->setByteLength(size);
          send(msg, "port$o", 0);

          sequence++;
          flow_size-=size;

          if(flowlet_size < 0){
              flowlet_count++;
              if(flowlet_count >= number_of_flowlet){
                  finish();
              }
              else{
                  sequence = 0;
                  arrival_time = INTER_ARRIVAL_TIME_BETWEEN_FLOWLETS;
                  flowlet_size = flow_size/number_of_flowlet;
              }
          }
          else {
              arrival_time = INTER_ARRIVAL_TIME_BETWEEN_PACKETS;
          }
          scheduleAt(simTime() + exponential(arrival_time),genpack);
          break;
          }
    }
}

uint64_t Host::draw_flow_size(){
    std::ifstream ifs(PATH_DISTRIBUTION);
    std::string line;
    uint64_t result;

    float y,x = uniform(0, 1);

    return (uint64_t)uniform(0,1000000)

}
}; // namespace
