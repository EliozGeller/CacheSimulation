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



#include <fstream>
#include <iostream>
#include <string>
#include <stdlib.h>     /* atoi */





namespace cachesimulation {

Define_Module(Rack);

void Rack::initialize()
{
    simtime_t arrival_time;
    uint64_t destination;

    int_to_ip(5);

    id = getIndex();
    file_pointer = 0;

    std::string path = PATH;
    path.append(std::to_string(id));
    path.append(".json");


    std::ifstream ifs(path);
    trace = json::parse(ifs);

    //generate first packet:
    DataPacket *message = new DataPacket("Generate packet message");
    message->setKind(GENERATEPACKET);
    generate_new_packet(message);


    EV << "trace size : "<< trace.size()<< endl;
}

void Rack::handleMessage(cMessage *message)
{
    simtime_t arrival_time;
    uint64_t new_destination;
   switch(message->getKind()){
        case GENERATEPACKET:
          DataPacket *genpack = check_and_cast<DataPacket *>(message);
          DataPacket *msg = new DataPacket("Data Packet");
          msg->setKind(DATAPACKET);
          uint64_t destination = genpack->getDestination();
          msg->setDestination(destination);
          msg->setId(genpack->getId());
          EV << "destination in rack = "<< destination<< endl;
          send(msg, "port$o", 0);



          if( file_pointer >= trace.size())return; //Checking whether the file of the traffic creator is finished


          //Generate new packet:
          generate_new_packet(genpack);
          break;
    }
}

void Rack::generate_new_packet(DataPacket *msg){
    simtime_t arrival_time;
    uint64_t destination;

    if(USE_TRAFFIC_GENERATOR == 1){// Generate from traffic generator
            arrival_time = (simtime_t)trace[file_pointer][3];
            std::string dest_string =  trace[file_pointer][1];
            destination = (uint64_t)std::stoi( dest_string );
    }
    else{// Generate exponential time
           arrival_time = simTime() + exponential(RACKRATE);
           destination = (uint64_t)uniform(0,POLICYSIZE);
    }
    msg->setDestination(destination);
    std::string id =  trace[file_pointer][4];
    msg->setId(id.c_str());
    scheduleAt(arrival_time,msg);
    file_pointer++;
}

}; // namespace
