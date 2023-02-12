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


simtime_t last_flow_a;



namespace cachesimulation {

Define_Module(Host);

void Host::initialize()
{


    //if we create traffic from file, there is no need for Host:
    if(getParentModule()->getParentModule()->par("create_offline_traffic").boolValue()){
        return;
    }


    //Read the distribution file:
    vector<vector<string>> size_distribution_file_string = read_data_file(getParentModule()->getParentModule()->par("size_distribution").stdstringValue());
    for(int i = 1 /*start from the second row*/;i < size_distribution_file_string.size();i++){
        vector<long double> row;
        if(size_distribution_file_string[i][0] == "" or size_distribution_file_string[i][1] == "")break;
        row.push_back(stoull(size_distribution_file_string[i][0]));
        row.push_back(stold(size_distribution_file_string[i][1]));
        size_distribution_file.push_back(row);
    }
    vector_distribution_file_size = size_distribution_file.size();

    //calculate the average_flow_size:
    for(int i = 1 /* begin from the second row in order to calculate */; i < vector_distribution_file_size;i++){
        average_flow_size += (size_distribution_file[i][1] - size_distribution_file[i - 1][1]) * size_distribution_file[i][0];
    }

    //cout << "average_flow_size = " << average_flow_size << endl;



    //set the inter_arrival_time_between_flows:

    long double total_rate_in_tor = stold(getParentModule()->getParentModule()->par("total_rate_in_tor").stdstringValue())/(getParentModule()->getParentModule()->par("scale").doubleValue());
    inter_arrival_time_between_flows = (simtime_t)((long double)(average_flow_size * 8)/(total_rate_in_tor)); // need to read from the file

    //0.000024329980000000
    //0.000018315995


    //inter_arrival_time_between_flowlets =  (simtime_t)stold( getParentModule()->getParentModule()->par("inter_arrival_time_between_flowlets").stdstringValue());

    policy_size =  stoull(getParentModule()->getParentModule()->par("policy_size").stdstringValue());
    large_flow = stoull(getParentModule()->getParentModule()->par("large_flow").stdstringValue()); /*100 Mbyte*/


    simtime_t start_time = (simtime_t)stold(par("flow_appearance").stdstringValue());
    EV << "start_time = " << start_time << endl;

    //set maximum of last flow appearance:
    if(start_time > (simtime_t)stold(getParentModule()->par("last_flow_appearance").stdstringValue())){
        getParentModule()->par("last_flow_appearance").setStringValue(my_to_string(start_time.dbl()));
    }




    //set the sub-net bounds of the destination:
    subnet_size = 5000;
    lower_bound_of_subnet = 1;//uniform(1,policy_size - subnet_size);
    higher_bound_of_subnet = min(lower_bound_of_subnet + subnet_size,policy_size);


    cMessage *pck = new cMessage("Set bounds to hosts");
    pck->setKind(BOUNDS_IN_HOSTS_PCK);
    scheduleAt(simTime() + START_TIME + 0.001,pck);

    start_flow(start_time);
}
void Host::start_flow(simtime_t arrival_time){

    if(genpack)cancelAndDelete(genpack);

    first = true;
    sequence = 0;
    id = getSimulation()->getUniqueNumber();


    //set the parameters of the flow:


    double x = 1.0/2.0;
    if(uniform(0,1) <= x){ //Application A:
        flow_size = draw_flow_size();
        destination = (uint64_t)uniform(1001,policy_size);
    }
    else { //Application B:
        flow_size = average_flow_size;
        destination = (uint64_t)uniform(1,1001);
    }

    rate = draw_rate(4000);

    inter_arrival_time_between_packets = (simtime_t)((1500.0*8.0)/rate);

    inter_arrival_time_between_flowlets = 100*inter_arrival_time_between_packets;

    //end parameters




    if(flow_size > large_flow){
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

    scheduleAt(arrival_time,message);
}


void Host::handleMessage(cMessage *message)
{
    int first_flag = 0,size_packet = 1500;



   simtime_t arrival_time;
   switch(message->getKind()){
        case GENERATEPACKET:
          {
              //mark the first packet in the flow:
              if(first){
                first_flag = 1;
                first = false;
              }
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
               if(flowlet_size <= size_packet)msg->setLast_packet(true);

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
              flowlet_count++;
              if(flowlet_count >= number_of_flowlet){// end of flow:
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
        case BOUNDS_IN_HOSTS_PCK:
        {
            lower_bound_of_subnet = (higher_bound_of_subnet + 1)%policy_size;
            higher_bound_of_subnet = min(lower_bound_of_subnet + subnet_size,policy_size);


            scheduleAt(simTime() + 0.001,message);
            break;
        }
    }
}

uint64_t Host::draw_flow_size(){
    /*
     * Here there is an option to check each row whether it is float or not,
     *  but right now it is just searching starting from the second row
     */

    float x = uniform(0,1);
    for(int i = 1 /*start from the second row*/;i < vector_distribution_file_size;i++){ //
        if(x <= size_distribution_file[i][1]){
            return (uint64_t)size_distribution_file[i][0];
        }
    }

    return 0;
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


void Host::finish(){
    cancelAndDelete(genpack);
}
}; // namespace
