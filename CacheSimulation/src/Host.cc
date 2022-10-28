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






namespace cachesimulation {

Define_Module(Host);

void Host::initialize()
{
    int flow_id =  getParentModule()->getIndex() * (int)getParentModule()->par("number_of_hosts") + getIndex();
    simtime_t start_time = (simtime_t)stold(par("flow_appearance").stdstringValue());

    //set maximum of id and last flow appearance:
    if(flow_id > stoi(getParentModule()->getParentModule()->par("last_flow_id").stdstringValue())){
        getParentModule()->getParentModule()->par("last_flow_id").setStringValue(to_string(flow_id));
    }
    if(start_time > (simtime_t)stold(getParentModule()->getParentModule()->par("last_flow_appearance").stdstringValue())){
        getParentModule()->getParentModule()->par("last_flow_appearance").setStringValue(my_to_string(start_time.dbl()));
    }

    start_flow(start_time,flow_id);
}
void Host::start_flow(simtime_t arrival_time,int flow_id){
    sequence = 0;
    id = flow_id;
    EV << "id in rack "<<  getParentModule()->getIndex() << " in Host "<< getIndex() << " is " << id << endl;
    //flow_size = stoull(par("flow_size").stdstringValue());
    flow_size = draw_flow_size();
    //flow_size = 100000;
    uint64_t policy_size =  stoull(getParentModule()->getParentModule()->par("policy_size").stdstringValue());
    destination = (uint64_t)uniform(1,policy_size); //change

    inter_arrival_time_between_packets =  (simtime_t)stold( getParentModule()->getParentModule()->par("inter_arrival_time_between_packets").stdstringValue());
    //inter_arrival_time_between_packets = 0.000000000003;
    inter_arrival_time_between_flowlets =  (simtime_t)stold( getParentModule()->getParentModule()->par("inter_arrival_time_between_flowlets").stdstringValue());

    EV << "inter_arrival_time_between_packets = "<< inter_arrival_time_between_packets << endl;
    EV << "inter_arrival_time_between_flowlets = "<< inter_arrival_time_between_flowlets << endl;


    if(flow_size > stoull(getParentModule()->getParentModule()->par("large_flow").stdstringValue()) /*100 Mbyte*/){
        number_of_flowlet = 10;
    }
    else {
        number_of_flowlet = 1;
    }
    flowlet_size = flow_size/number_of_flowlet;
    flowlet_count = 0;

    //generate first packet:
    cMessage *message = new cMessage("Generate packet message");
    genpack = message;
    message->setKind(GENERATEPACKET);



    EV << "id = "<< id << endl;
    EV << "arrival_time = "<< arrival_time << endl;
    EV << "flow_size = "<< flow_size << endl;
    EV << "flowlet_size = "<< flowlet_size << endl;
    scheduleAt(simTime() + arrival_time,message);
}

void Host::handleMessage(cMessage *message)
{

    //start of test:
    /*
    DataPacket *msg = new DataPacket("Data Packet");
    msg->setKind(DATAPACKET);
    msg->setDestination(destination);
    std::string str_id = create_id(id,flowlet_count,sequence);
    EV << "id = "<< str_id << endl;
    msg->setId(str_id.c_str());
    int size_packet = 1500;
    msg->setByteLength(size_packet);
    send(msg, "port$o", 0);
    scheduleAt(simTime() + exponential(inter_arrival_time_between_packets),message);
    return;
*/

    //end of test


    if(flowlet_count >= number_of_flowlet) return;

   simtime_t arrival_time;
   switch(message->getKind()){
        case GENERATEPACKET:
          {
          //creat data packet:

          DataPacket *msg = new DataPacket("Data Packet");
          msg->setKind(DATAPACKET);
          msg->setDestination(destination);
          std::string str_id = create_id(id,flowlet_count,sequence);
          EV << "id = "<< str_id << endl;
          msg->setId(str_id.c_str());
          int size_packet = 1500;
          msg->setByteLength(size_packet);

          //send the data packet:
          send(msg, "port$o", 0);



          //schedule the next packet or end the flow:
          sequence++;
          flowlet_size -= size_packet;
          EV << "flowlet_size = "<< flowlet_size << endl;
          if(flowlet_size < 0){
              flowlet_count++;
              if(flowlet_count >= number_of_flowlet){// end of flow:
                //callFinish();
                //deleteModule();

                //strat new flow:

                cancelAndDelete(genpack);
                int flow_id = stoi(getParentModule()->getParentModule()->par("last_flow_id").stdstringValue()) + 1;
                long double inter_arrival_time_between_flows = stold(getParentModule()->getParentModule()->par("inter_arrival_time_between_flows").stdstringValue());
                simtime_t start_time = (simtime_t)stold(getParentModule()->getParentModule()->par("last_flow_appearance").stdstringValue()) + exponential(inter_arrival_time_between_flows);



                start_flow(start_time,flow_id);
                //end start new flow
                return;
              }
              else{
                  EV <<"END OF flowlet"<<endl;
                  sequence = 0;
                  arrival_time = inter_arrival_time_between_flowlets;
                  flowlet_size = flow_size/number_of_flowlet;
              }
          }
          else {
              arrival_time = inter_arrival_time_between_packets;
          }


          //delete message;
          //m = new cMessage("Generate packet message");
          genpack = message;
          scheduleAt(simTime() + exponential(arrival_time),message);

          break;
          }//end case
    }
}

uint64_t Host::draw_flow_size(){
    /*
     * Here there is an option to check each row whether it is float or not,
     *  but right now it is just searching starting from the second row
     */
    vector<vector<string>> size_distribution_file = read_data_file(PATH_DISTRIBUTION);


    float x = uniform(0,1);
    for(int i = 1 /*start from the second row*/;i < size_distribution_file.size();i++){ //
        if(x < stold(size_distribution_file[i][1])){
            return (uint64_t)stoull(size_distribution_file[i][0]);
        }
    }
}


void Host::finish(){
    cancelAndDelete(genpack);
}
}; // namespace
