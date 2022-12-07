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




#include "Destination.h"
#include "Definitions.h"

#include <iostream>
#include <fstream>
using namespace std;



namespace cachesimulation {

Define_Module(Destination);

void Destination::initialize()
{
    miss_count.setName("miss count");
    out_of_order.setName("out of order");
    byte_counter = 0;


    //new Histogram;
    bandwidth_hist.setName("bandwidth hist");
    cMessage *hist_msg = new cMessage("hist_msg");
    hist_msg->setKind(HIST_MSG);
    scheduleAt(simTime() + START_TIME + TIME_INTERVAL_FOR_OUTPUTS,hist_msg);

    cMessage *m = new cMessage("flow_count");
    m->setKind(INTERVAL_PCK);
    scheduleAt(simTime() + START_TIME + INTERVAL,m);
    //end new histogram

    //set the dir:
    dir = getParentModule()->par("output_file").stdstringValue();
    EV << dir[0] << endl;


    recordScalar("run_elephant: ",getParentModule()->par("run_elephant").boolValue());
}

void Destination::handleMessage(cMessage *message)
{


    switch(message->getKind()){
    case HITPACKET:
    case DATAPACKET:
    {
        DataPacket *msg = check_and_cast<DataPacket *>(message);
        byte_counter += msg->getBitLength();
        EV <<" id = " <<msg->getId() << endl;

        //statistics for miss count
        miss_count.collect(msg->getMiss_hop());

        //statistics for out of order
        long long int diff = out_of_order_statistics(msg);


        //miss_count_map:
        unsigned int flow_size = msg->getFlow_size();
        int rate =  rate_to_bin(msg->getRate());

        EV << "rate = " << rate << "   org = " << msg->getRate()<<endl;

        miss_count_map[std::make_pair(flow_size,rate)] = std::make_pair(miss_count_map[std::make_pair(flow_size,rate)].first + 1,miss_count_map[std::make_pair(flow_size,rate)].second + msg->getMiss_hop());
        out_of_order_map[std::make_pair(flow_size,rate)] = std::make_pair(out_of_order_map[std::make_pair(flow_size,rate)].first + 1,out_of_order_map[std::make_pair(flow_size,rate)].second + diff);


        delete msg;
        //cancelAndDelete(msg);

        break;
    }
    case INTERVAL_PCK:
    {
       bandwidth_hist.collect((long double)(byte_counter*8)/(long double)(INTERVAL*1000000000.0));
       byte_counter = 0;

       scheduleAt(simTime() + INTERVAL,message);
       break;
    }
    case HIST_MSG://histogram per 1 sec:
    {
        //handle bandwidth_hist:
        string name =  "";
        simtime_t t = simTime() - TIME_INTERVAL_FOR_OUTPUTS,t1 =  simTime();
        name =  name + my_to_string(t.dbl()) + "  -  " + my_to_string(t1.dbl());
        bandwidth_hist.recordAs(name.c_str());


        //handle miss count/out of order"
        miss_count.recordAs(name.c_str());
        out_of_order.recordAs(name.c_str());

        //print  maps:
        ofstream MyFile(dir + name + ".txt");
        //print miss count:
        MyFile << "#######################################################\nmiss_count_map:{size,rate,count,value}\n{\n";
        for( std::map<std::pair<unsigned int,unsigned long long int>, std::pair<unsigned long long int,unsigned long long int>>::const_iterator it = miss_count_map.begin();
          it != miss_count_map.end(); ++it)
        {
          MyFile << "{" << it->first.first << "," << it->first.second << "," << it->second.first << "," << it->second.second << "},\n";
        }
        MyFile << "}"<< std::endl;

        ////print out of order:
        MyFile << "#######################################################\nout of order:{size,rate,count,value}\n{\n";
        for( std::map<std::pair<unsigned int,unsigned long long int>, std::pair<unsigned long long int,unsigned long long int>>::const_iterator it = out_of_order_map.begin();
          it != out_of_order_map.end(); ++it)
        {
           MyFile << "{" << it->first.first << "," << it->first.second << "," << it->second.first << "," << it->second.second << "},\n";
        }
        MyFile << "}"<< std::endl;
        MyFile.close();

        scheduleAt(simTime() + TIME_INTERVAL_FOR_OUTPUTS,message);
        break;
    }
    }
}

long long int Destination::out_of_order_statistics(DataPacket* msg)
{
    long long int diff = get_sequence(msg->getId()) - expected_sequence[get_flow(msg->getId())];
    out_of_order.collect(diff);
    expected_sequence[get_flow(msg->getId())] = get_sequence(msg->getId());
    return diff;
}

void Destination::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Miss count in the Destination, mean:   " << miss_count.getMean() << endl;
    EV << "Total arrived packets in the Destination:   " << byte_counter << endl;
    EV << "simtime =    " << simTime() << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    miss_count.recordAs("miss count");
    out_of_order.recordAs("out of order");
}





}; // namespace
