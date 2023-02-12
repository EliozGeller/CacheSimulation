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
#include <fstream>
#include <iostream>
#include <map>


#define TRAFFIC_STRUCTURE_SIZE 10000000
//#define TRAFFIC_STRUCTURE_SIZE 500

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Hub : public cSimpleModule
{
private:
    unsigned long long int byte_count = 0;
    unsigned long long int window_byte_count = 0;
    unsigned long long int flowlet_count_size = 0;
    cOutVector flowlet_count;
    cHistogram bandwidth_hist;
    cHistogram bandwidth_hist_per_sec;
    simtime_t end_time = 0;

    //record or create traffic:
    ofstream traffic_file;
    fstream traffic_file_create;
    string traffic_structure[TRAFFIC_STRUCTURE_SIZE];
    unsigned int traffic_structure_current_index = 0;
    bool record_traffic;
    bool create_offline_traffic;
    simtime_t traffic_interval = 0.25;
    simtime_t last_traffic_interval = 0;
  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual void finish();
};

}; // namespace

#endif

#include <map>


namespace cachesimulation {

Define_Module(Hub);

void Hub::initialize()
{
    bandwidth_hist.setName("bandwidth hist");
    bandwidth_hist_per_sec.setName("bandwidth_hist_per_sec");
    flowlet_count.setName("flowlet_count");

    //Initialize window size process
    cMessage *m = new cMessage("bandwidth hist");
    m->setKind(INTERVAL_PCK);
    scheduleAt(simTime() + START_TIME + INTERVAL,m);


    //Initialize plot histograms process
    cMessage *hist_msg = new cMessage("hist_msg");
    hist_msg->setKind(HIST_MSG);
    scheduleAt(simTime() + START_TIME + TIME_INTERVAL_FOR_OUTPUTS,hist_msg);


    ////Initialize record or create traffic process
    record_traffic =  getParentModule()->getParentModule()->par("record_traffic").boolValue();
    create_offline_traffic = getParentModule()->getParentModule()->par("create_offline_traffic").boolValue();
    if(record_traffic or create_offline_traffic){
        string name = "traffic";

        if(record_traffic)traffic_file.open(name + my_to_string((int)getParentModule()->getIndex()) + ".csv");
        //if(record_traffic)traffic_file.open("a.csv");
        if(create_offline_traffic)traffic_file_create.open(name + my_to_string((int)getParentModule()->getIndex()) + ".csv", ios::in);
        //if(create_offline_traffic)traffic_file_create.open("a.csv", ios::in);


    }


    //Create traffic from file:
    if(create_offline_traffic){
        //Read chunk from the file:
        string line;
        for(unsigned int i = 0;i <  TRAFFIC_STRUCTURE_SIZE;i++){
            getline(traffic_file_create, line);
            traffic_structure[i] = line;
            if(line == "")break;
        }

        //Create Data Packet;
        DataPacket *p = new DataPacket("Data Packet");
        p->setKind(DATAPACKET);




        p->setDestination(stoull(mysplitstring(traffic_structure[traffic_structure_current_index],",",2)));
        std::string str_id = mysplitstring(traffic_structure[traffic_structure_current_index],",",1);
        EV << "id = "<< str_id << endl;
        p->setId(str_id.c_str());
        p->setByteLength(1500);
        p->setFlow_size(stoull(mysplitstring(traffic_structure[traffic_structure_current_index],",",3)));
        p->setRate(stoull(mysplitstring(traffic_structure[traffic_structure_current_index],",",4)));

        if(stoi(mysplitstring(str_id,".",1)) + stoi(mysplitstring(str_id,".",2)) == 0)p->setFirst_packet(true);
        //if(flowlet_size <= size_packet)p->setLast_packet(true);

        simtime_t timestamp = (simtime_t)stold(mysplitstring(traffic_structure[traffic_structure_current_index],",",0));
        scheduleAt(timestamp,p);
    }


}

void Hub::handleMessage(cMessage *msg)
{

    int pck_kind = msg->getKind();
    //Plot histograms:
    if(pck_kind == HIST_MSG){
       string name =  "";
       simtime_t t = simTime() - TIME_INTERVAL_FOR_OUTPUTS,t1 =  simTime();
       name =  name + my_to_string(t.dbl()) + "  -  " + my_to_string(t1.dbl());
       string name1 = name + ":bandwidth_hist_per_";
       bandwidth_hist_per_sec.recordAs(name1.c_str());
       bandwidth_hist_per_sec.clear();

       scheduleAt(simTime() + TIME_INTERVAL_FOR_OUTPUTS,msg);
       return;
    }
    //end Plot histograms:


    //Collect data at window size:
    if(pck_kind == INTERVAL_PCK){
        bandwidth_hist.collect((long double)(window_byte_count*8)/(long double)(INTERVAL));
        bandwidth_hist_per_sec.collect((long double)(window_byte_count*8)/(long double)(INTERVAL));
        window_byte_count = 0;

        scheduleAt(simTime() + INTERVAL,msg);

        return;
    }
    //End Collect data at window size





    // data packet from here:
    DataPacket *m = check_and_cast<DataPacket *>(msg);




    //byte count:
    byte_count += m->getByteLength();
    window_byte_count += m->getByteLength();
    flowlet_count_size += m->getFirst_packet()*m->getFlow_size();
    //end byte count


    //record packet:
    if(record_traffic){
        string s = ""; //The string structure: "timestamp,flow id,destination,flow size,flow rate"
        traffic_structure[traffic_structure_current_index] = s + my_to_string(simTime().dbl()) + "," + (string)m->getId() + ","
                   + my_to_string(m->getDestination()) + "," + my_to_string(m->getFlow_size())+ "," + my_to_string(m->getRate());


       traffic_structure_current_index++;
       if(traffic_structure_current_index == TRAFFIC_STRUCTURE_SIZE){
           for(unsigned int i = 0; i < TRAFFIC_STRUCTURE_SIZE;i++){
               traffic_file <<  traffic_structure[i] << endl;
           }
           traffic_structure_current_index = 0;
       }
    }

    //end record packet


    //Create traffic from file:
    if(create_offline_traffic){
        traffic_structure_current_index++;
        if(traffic_structure_current_index == TRAFFIC_STRUCTURE_SIZE){
            //Read chunk from the file:
            string line;
            for(unsigned int i = 0;i <  TRAFFIC_STRUCTURE_SIZE;i++){
                getline(traffic_file_create, line);
                traffic_structure[i] = line;
                if(line == "")break;
            }
            traffic_structure_current_index = 0;
        }


        if(traffic_structure[traffic_structure_current_index] == ""){
            create_offline_traffic = false;
        }
        else{
            //Create Data Packet;
            DataPacket *p = new DataPacket("Data Packet");
            p->setKind(DATAPACKET);


            p->setDestination(stoull(mysplitstring(traffic_structure[traffic_structure_current_index],",",2)));
            std::string str_id = mysplitstring(traffic_structure[traffic_structure_current_index],",",1);
            EV << "id = "<< str_id << endl;
            p->setId(str_id.c_str());
            p->setByteLength(1500);
            p->setFlow_size(stoull(mysplitstring(traffic_structure[traffic_structure_current_index],",",3)));
            p->setRate(stoull(mysplitstring(traffic_structure[traffic_structure_current_index],",",4)));

            if(stoi(mysplitstring(str_id,".",1)) + stoi(mysplitstring(str_id,".",2)) == 0)p->setFirst_packet(true);
            //if(flowlet_size <= size_packet)p->setLast_packet(true);

            simtime_t timestamp = (simtime_t)stold(mysplitstring(traffic_structure[traffic_structure_current_index],",",0));
            scheduleAt(timestamp,p);
        }

    }
    //End of Create file



    //forward the packet:
    send(msg, "port$o", 0);
}

void Hub::finish(){
    EV << "Bandwidth in Hub: "<< (long double)(byte_count*8)/simTime().dbl()<< "bps"<< endl;

    bandwidth_hist.recordAs("bandwidth hist");
    traffic_file.close();


}
}; // namespace
