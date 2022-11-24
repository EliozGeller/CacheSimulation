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

    inter_arrival_time_between_flowlets =  (simtime_t)stold( getParentModule()->getParentModule()->par("inter_arrival_time_between_flowlets").stdstringValue());
    inter_arrival_time_between_flows = (simtime_t)stold(getParentModule()->getParentModule()->par("inter_arrival_time_between_flows").stdstringValue());


    simtime_t start_time = (simtime_t)stold(par("flow_appearance").stdstringValue());
    EV << "start_time = " << start_time << endl;

    //set maximum of id and last flow appearance:
    if(start_time > (simtime_t)stold(getParentModule()->par("last_flow_appearance").stdstringValue())){
        getParentModule()->par("last_flow_appearance").setStringValue(my_to_string(start_time.dbl()));
    }


    //later_start:
    long double avg_flow_size = 4865995.738;
    long double avg_rate = 2.5*1000000000;
    simtime_t avg_transmination_time_of_flow = (long double)(avg_flow_size*8)/avg_rate + (((avg_flow_size > stoull(getParentModule()->getParentModule()->par("large_flow").stdstringValue())) ? 10 : 1) - 1)*inter_arrival_time_between_flowlets.dbl();
    uint64_t n = (uint64_t)((START_TIME - start_time)/(avg_transmination_time_of_flow + inter_arrival_time_between_flows));

    simtime_t new_start_time = n*(avg_transmination_time_of_flow + inter_arrival_time_between_flows);
    EV << "XXXX = "<< new_start_time << endl;

    start_flow(start_time);
}
void Host::start_flow(simtime_t arrival_time){

    if(genpack)cancelAndDelete(genpack);

    first = true;
    sequence = 0;
    id = getSimulation()->getUniqueNumber();
    EV <<"Start flow!!" << endl;
    EV << "id in rack "<<  getParentModule()->getIndex() << " in Host "<< getIndex() << " is " << id << endl;
    //flow_size = stoull(par("flow_size").stdstringValue());
    flow_size = draw_flow_size();
    if(arrival_time == 0.0)flow_size = 0.5*flow_size;
    //flow_size = 100000;
    uint64_t policy_size =  stoull(getParentModule()->getParentModule()->par("policy_size").stdstringValue());
    destination = (uint64_t)uniform(1,policy_size); //change

    //inter_arrival_time_between_packets =  (simtime_t)stold( getParentModule()->getParentModule()->par("inter_arrival_time_between_packets").stdstringValue());//real one

    //test:
    rate = draw_rate(4000);
    //long double rate = 500000000*pow(1.0/(1.0 - uniform(0,1)),1.0 / 1.0256410256410255);

    inter_arrival_time_between_packets = (simtime_t)((1500.0*8.0)/rate);
    EV << "Rate = "<< rate << " bps" << endl;
    //end test


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
    scheduleAt(arrival_time,message);
}

long double Host::draw_rate(int mean){
    long double rate;
    switch(mean){
    case 40:
        rate =  5 * 1000000*pow(1.0/(1.0 - uniform(0,1)),1.0 / 1.0256410256410255);
        break;
    case 400:
        rate =  50 * 1000000*pow(1.0/(1.0 - uniform(0,1)),1.0 / 1.0256410256410255);
        break;
    case 4000:
        rate =  500 * 1000000*pow(1.0/(1.0 - uniform(0,1)),1.0 / 1.0256410256410255);
        break;
    case 40000:
        rate =  5000000000*pow(1.0/(1.0 - uniform(0,1)),1.0 / 1.0256410256410255);
        break;
    }
    if(rate > 40000000000.0) rate = 40000000000.0;
    return rate;
}

void Host::handleMessage(cMessage *message)
{
    int first_flag = 0,size_packet = 1500;

    if(first){
          first_flag = 1;
          first = false;
    }

   simtime_t arrival_time;
   switch(message->getKind()){
        case GENERATEPACKET:
          {
          //creat data packet:
          if(simTime()>= START_TIME){
              DataPacket *msg = new DataPacket("Data Packet");
              msg->setKind(DATAPACKET);
              msg->setDestination(destination);
              std::string str_id = create_id(id,flowlet_count,sequence);
              EV << "id = "<< str_id << endl;
              msg->setId(str_id.c_str());
              msg->setByteLength(size_packet);
              msg->setFlow_size(flow_size);
              msg->setRate(rate);

              msg->setFirst_packet(first_flag);

              //send the data packet:
              send(msg, "port$o", 0);
          }

          //Checking whether the flow ends before the start of the time
          else{
              simtime_t transmination_time_of_flow = (long double)flow_size/rate + (number_of_flowlet - 1)*inter_arrival_time_between_flowlets.dbl();
              if(((simTime() + transmination_time_of_flow) < START_TIME) && first){
                  //flowlet_count = number_of_flowlet + 1;
                  //flowlet_size = -1;

                  simtime_t start_time = (simtime_t)(stold(getParentModule()->par("last_flow_appearance").stdstringValue()) + exponential(inter_arrival_time_between_flows));
                  getParentModule()->par("last_flow_appearance").setStringValue(my_to_string(start_time.dbl()));

                  start_flow(start_time);
                  return;
              }
          }



          //schedule the next packet or end the flow:
          sequence++;
          flowlet_size -= size_packet;
          EV << "flowlet_size = "<< flowlet_size << endl;


          if(flowlet_size < 0){
              //send last message:
              if(simTime()>= START_TIME){
                  DataPacket *ma = new DataPacket("Data Packet");
                  ma->setKind(DATAPACKET);
                  std::string str_id1 = create_id(id,flowlet_count,sequence);
                  ma->setId(str_id1.c_str());
                  ma->setExternal_destination(1001);
                  send(ma, "port$o", 0);
              }

              //end send last message


              flowlet_count++;
              if(flowlet_count >= number_of_flowlet){// end of flow:
                //callFinish();
                //deleteModule();



                //strat new flow:
                simtime_t start_time = (simtime_t)(stold(getParentModule()->par("last_flow_appearance").stdstringValue()) + exponential(inter_arrival_time_between_flows));
                getParentModule()->par("last_flow_appearance").setStringValue(my_to_string(start_time.dbl()));



                start_flow(start_time);
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
        if(x <= stold(size_distribution_file[i][1])){
            return (uint64_t)stoull(size_distribution_file[i][0]);
        }
    }

    return 0;
}


void Host::finish(){
    cancelAndDelete(genpack);
}
}; // namespace
